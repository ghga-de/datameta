# Copyright 2021 Universität Tübingen, DKFZ and EMBL for the German Human Genome-Phenome Archive (GHGA)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
from dataclasses import dataclass
from pyramid.httpexceptions import HTTPForbidden, HTTPNotFound, HTTPNoContent
from pyramid.view import view_config
from pyramid.request import Request
from sqlalchemy.orm import joinedload
from sqlalchemy import and_
from typing import Optional, Dict, List
from ..linting import validate_metadataset_record
from .. import security, siteid, resource, validation
from ..models import MetaDatum, MetaDataSet, ServiceExecution, Service, MetaDatumRecord, Submission, File
from ..security import authz
import datetime
from datetime import timezone
from ..resource import resource_by_id, resource_query_by_id, get_identifier
from ..utils import get_record_from_metadataset
from . import DataHolderBase
from .. import errors
from .metadata import get_all_metadata, get_service_metadata, get_metadata_with_access

log = logging.getLogger(__name__)


@dataclass
class MetaDataSetServiceExecution(DataHolderBase):
    service_execution_id   : dict
    execution_time         : str  # ISO format
    service_id             : dict
    user_id                : dict


@dataclass
class MetaDataSetResponse(DataHolderBase):
    """MetaDataSetResponse container for OpenApi communication"""
    id                   : dict
    record               : Dict[str, Optional[str]]
    file_ids             : Dict[str, Optional[Dict[str, str]]]
    user_id              : str
    submission_id        : Optional[str] = None
    service_executions   : Optional[Dict[str, Optional[MetaDataSetServiceExecution]]] = None

    @staticmethod
    def from_metadataset(metadataset: MetaDataSet, metadata_with_access: Dict[str, MetaDatum]):
        """Creates a MetaDataSetResponse from a metadataset database object and
        a dictionary of metadata [MetaDatum.name, MetaDatum] that the receiving
        user has read access to."""

        # Identify file ids associated with this metadataset for metadata with access
        file_ids = { mdrec.metadatum.name : resource.get_identifier_or_none(mdrec.file)
                for mdrec in metadataset.metadatumrecords
                if mdrec.metadatum.isfile and mdrec.metadatum.name in metadata_with_access}
        # Build the metadataset response
        return MetaDataSetResponse(
                id                 = get_identifier(metadataset),
                record             = get_record_from_metadataset(metadataset, metadata_with_access),
                file_ids           = file_ids,
                user_id            = get_identifier(metadataset.user),
                submission_id      = get_identifier(metadataset.submission) if metadataset.submission else None,
                service_executions = collect_service_executions(metadata_with_access, metadataset)
                )


def record_to_strings(record: Dict[str, str]):
    return {
        k: str(v) if v is not None else None
        for k, v in record.items()
    }


def render_record_values(metadata: Dict[str, MetaDatum], record: dict) -> dict:
    """Renders values of a metadataset record. Please note: the record should already have passed validation."""
    record_rendered = record.copy()
    for field in metadata:
        if field not in record_rendered:
            # if field is not contained in record, add it as None to the record:
            record_rendered[field] = None
            continue
        elif record_rendered[field] and metadata[field].datetimefmt:
            # if MetaDatum is a datetime field, render the value in isoformat
            record_rendered[field] = datetime.datetime.strptime(
                    record_rendered[field],
                    metadata[field].datetimefmt
                    ).isoformat()
    return record_rendered


def delete_staged_metadataset_from_db(mdata_id, db, auth_user, request):
    # Find the requested metadataset
    mdata_set = resource_by_id(db, MetaDataSet, mdata_id)

    # Check if the metadataset exists
    if not mdata_set:
        raise HTTPNotFound()

    # Check if user owns this metadataset
    if not authz.delete_mset(auth_user, mdata_set):
        raise HTTPForbidden()

    # Check if the metadataset was already submitted
    if mdata_set.submission:
        raise errors.get_not_modifiable_error()

    # Delete the records
    request.dbsession.query(MetaDatumRecord).filter(MetaDatumRecord.metadataset_id == mdata_set.id).delete()

    # Delete the metadataset
    db.delete(mdata_set)


@view_config(
    route_name      = "rpc_delete_metadatasets",
    renderer        = "json",
    request_method  = "POST",
    openapi         = True
)
def delete_metadatasets(request: Request) -> HTTPNoContent:
    # Check authentication or raise 401
    auth_user = security.revalidate_user(request)

    db = request.dbsession

    for mdata_id in set(request.openapi_validated.body["metadatasetIds"]):
        delete_staged_metadataset_from_db(mdata_id, db, auth_user, request)

    return HTTPNoContent()


@view_config(
    route_name="metadatasets",
    renderer='json',
    request_method="POST",
    openapi=True
)
def post(request: Request) -> MetaDataSetResponse:
    """Create new metadataset"""
    auth_user = security.revalidate_user(request)
    db = request.dbsession

    # Obtain string converted version of the record
    record = record_to_strings(request.openapi_validated.body["record"])

    # Query the configured metadata. We're only considering and allowing
    # non-service metadata when creating a new metadataset.
    metadata = get_all_metadata(db, include_service_metadata=False)

    # prevalidate (raises 400 in case of validation failure):
    validate_metadataset_record(metadata, record)

    # Render records according to MetaDatum constraints.
    record = render_record_values(metadata, record)

    # construct new MetaDataSet:
    mdata_set = MetaDataSet(
        site_id = siteid.generate(request, MetaDataSet),
        user_id = auth_user.id,
        submission_id = None
    )
    db.add(mdata_set)
    db.flush()

    # Add NULL values for service metadata
    service_metadata = get_service_metadata(db)
    for s_mdatum in service_metadata.values():
        mdatum_rec = MetaDatumRecord(
                metadatum_id     = s_mdatum.id,
                metadataset_id   = mdata_set.id,
                file_id          = None,
                value            = None
                )
        db.add(mdatum_rec)

    # Add the non-service metadata as specified in the request body
    for name, value in record.items():
        mdatum_rec = MetaDatumRecord(
            metadatum_id     = metadata[name].id,
            metadataset_id   = mdata_set.id,
            file_id          = None,
            value            = value
        )
        db.add(mdatum_rec)

    return MetaDataSetResponse(
        id              = get_identifier(mdata_set),
        record          = record,
        file_ids        = { name : None for name, metadatum in metadata.items() if metadatum.isfile },
        user_id         = get_identifier(mdata_set.user),
        submission_id   = get_identifier(mdata_set.submission) if mdata_set.submission else None,
    )


def collect_service_executions(metadata_with_access: Dict[str, MetaDatum], mdata_set: MetaDataSet) -> Optional[Dict[str, Optional[MetaDataSetServiceExecution]]]:
    # Collect service metadata from provided metadata with access
    service_metadata = { name : mdatum for name, mdatum in metadata_with_access.items() if mdatum.service_id is not None }
    # If there are service metadata among the metadata with access, we're returning a dict, otherwise None
    service_executions = None
    if service_metadata:
        ids = { mdatum.id for mdatum in service_metadata.values() }
        service_executions = {}
        # Collect service executions related to this metadataset and store them
        # if they relate to the service metadata with access
        for sexec in mdata_set.service_executions:
            for s_mdatum in sexec.service.target_metadata:
                if s_mdatum.id in ids:
                    service_executions[s_mdatum.name] = sexec

        # Collect all other service metadata for which no service execution
        # could be found and annotate 'None' for those
        for s_mdatum_name in service_metadata.keys():
            if s_mdatum_name not in service_executions:
                service_executions[s_mdatum_name] = None

        # Transform the ServiceExecution database objects into
        # MetaDataSetServiceExecution objects
        service_executions = { name : MetaDataSetServiceExecution(
            service_execution_id   = get_identifier(sexec),
            execution_time         = sexec.datetime.isoformat() + '+00:00',  # Assuming UTC datetimes in the database
            service_id             = get_identifier(sexec.service),
            user_id                = get_identifier(sexec.user)
            ) if sexec is not None else None for name, sexec in service_executions.items() }
    return service_executions


@view_config(
    route_name="metadatasets",
    renderer='json',
    request_method="GET",
    openapi=True
)
def get_metadatasets(request: Request) -> List[MetaDataSetResponse]:
    """Query metadatasets according to filtering critera"""
    auth_user = security.revalidate_user(request)
    db = request.dbsession

    # GET parameters
    submitted_after = request.openapi_validated.parameters.query.get('submittedAfter')
    submitted_before = request.openapi_validated.parameters.query.get('submittedBefore')
    awaiting_service = request.openapi_validated.parameters.query.get('awaitingService')

    # Query metadata sets and join entities that we are going to use.
    # NOTE: JOINing 'Submission' reduces to submitted metadatasets and enables
    # filtering on Submission attributes
    query = db.query(MetaDataSet)\
            .join(Submission)\
            .options(joinedload(MetaDataSet.service_executions).joinedload(ServiceExecution.user))\
            .options(joinedload(MetaDataSet.service_executions).joinedload(ServiceExecution.service).joinedload(Service.target_metadata))\
            .options(joinedload(MetaDataSet.metadatumrecords).joinedload(MetaDatumRecord.metadatum))\
            .options(joinedload(MetaDataSet.metadatumrecords).joinedload(MetaDatumRecord.file))\
            .options(joinedload(MetaDataSet.submission))

    # Check which metadata of this metadataset the user is allowed to view
    metadata_with_access = get_metadata_with_access(db, auth_user)

    # Collect services of service metadata the user is allowed to read
    readable_services = { metadatum.service for metadatum in metadata_with_access.values() if metadatum.service is not None }
    readable_services_by_id = {}
    for service in readable_services:
        readable_services_by_id[service.uuid]      = service
        readable_services_by_id[service.site_id]   = service

    # Check whether we need to filter for the user's group
    if not authz.view_mset_any(auth_user):
        query = query.filter(Submission.group_id == auth_user.group_id)

    # Apply query filters
    if submitted_after is not None:
        query = query.filter(Submission.date > submitted_after.astimezone(timezone.utc))
    if submitted_before is not None:
        query = query.filter(Submission.date < submitted_before.astimezone(timezone.utc))
    if awaiting_service is not None:
        if awaiting_service not in readable_services_by_id:
            raise errors.get_validation_error(messages=['Invalid service ID specified'], fields=['awaitingServices'])
        query = query.outerjoin(ServiceExecution, and_(
            MetaDataSet.id == ServiceExecution.metadataset_id,
            ServiceExecution.service_id == readable_services_by_id[awaiting_service].id
            )).filter(ServiceExecution.id.is_(None))

    # Execute the query
    mdata_sets = query.all()

    # No results? Return 404
    if not mdata_sets:
        raise HTTPNotFound()

    log.info("User queried MetaDataSets.", extra={"user_id": auth_user.id})
    return [
            MetaDataSetResponse.from_metadataset(mdata_set, metadata_with_access)
            for mdata_set in mdata_sets
            ]


@view_config(
    route_name="metadatasets_id",
    renderer='json',
    request_method="GET",
    openapi=True
)
def get_metadataset(request: Request) -> MetaDataSetResponse:
    """Get a metadataset by ID"""
    auth_user = security.revalidate_user(request)
    db = request.dbsession

    # Query the targeted metadataset and join the related entities that we are
    # going to access
    mdata_set = resource_query_by_id(db, MetaDataSet, request.matchdict['id'])\
            .options(joinedload(MetaDataSet.service_executions).joinedload(ServiceExecution.user))\
            .options(joinedload(MetaDataSet.service_executions).joinedload(ServiceExecution.service).joinedload(Service.target_metadata))\
            .options(joinedload(MetaDataSet.metadatumrecords).joinedload(MetaDatumRecord.metadatum))\
            .options(joinedload(MetaDataSet.metadatumrecords).joinedload(MetaDatumRecord.file))\
            .options(joinedload(MetaDataSet.submission))\
            .one_or_none()

    # Check if the metadataset exists
    if not mdata_set:
        raise HTTPNotFound()

    # Check if the user is allowed to view this metadataset
    if not authz.view_mset(auth_user, mdata_set):
        raise HTTPForbidden()

    # Check which metadata of this metadataset the user is allowed to view
    if mdata_set.submission_id is None:
        metadata_with_access = get_all_metadata(db, include_service_metadata=False)
    else:
        metadata_with_access = get_metadata_with_access(db, auth_user)

    log.info("Returned a MetaDataSet by its ID.", extra={"user_id": auth_user.id, "metadataset_id": request.matchdict['id']})
    # Check and annotate service executions
    return MetaDataSetResponse.from_metadataset(mdata_set, metadata_with_access)


@view_config(
    route_name="metadatasets_id",
    renderer='json',
    request_method="DELETE",
    openapi=True
)
def delete_metadataset(request: Request) -> HTTPNoContent:
    # Check authentication or raise 401
    auth_user = security.revalidate_user(request)

    db = request.dbsession

    delete_staged_metadataset_from_db(request.matchdict['id'], db, auth_user, request)

    return HTTPNoContent()


@view_config(
    route_name="service_execution",
    renderer='json',
    request_method="POST",
    openapi=True
)
def set_metadata_via_service(request: Request) -> MetaDataSetResponse:
    """Endpoint for the submission of results of a service execution."""

    # Check authentication or raise 401
    auth_user = security.revalidate_user(request)
    db = request.dbsession

    # Query the specified resources
    metadataset = resource.resource_query_by_id(db, MetaDataSet, request.matchdict['metadatasetId'])\
            .options(joinedload(MetaDataSet.service_executions).joinedload(ServiceExecution.service))\
            .options(joinedload(MetaDataSet.metadatumrecords).joinedload(MetaDatumRecord.metadatum))\
            .one_or_none()

    service = resource.resource_query_by_id(db, Service, request.matchdict['serviceId'])\
            .options(joinedload(Service.target_metadata))\
            .options(joinedload(Service.users))\
            .one_or_none()

    # Return 404 if a resource could not be found
    if metadataset is None or service is None:
        raise HTTPNotFound()

    service_metadata = { mdatum.name : mdatum for mdatum in service.target_metadata }

    service_records = { rec.metadatum.name : rec for rec in metadataset.metadatumrecords if rec.metadatum.name in service_metadata }

    # Return 403 if the user has no permission to execute this service or the
    # service has already been executed for this metadataset
    if service.id in (sexec.service_id for sexec in metadataset.service_executions):
        raise HTTPForbidden(json_body={})

    if not authz.execute_service(auth_user, service):
        raise HTTPForbidden(json_body={})

    # Try to associate all metadata in the request body with the service metadata
    records = record_to_strings(request.openapi_validated.body["record"])
    val_errors = []  # tuples (message, field)
    for mdatum_name in records:
        if mdatum_name not in (target_metadatum.name for target_metadatum in service.target_metadata):
            val_errors.append(("Metadatum unknown or not associated with the specified service.", mdatum_name))

    # If there were any validation errors, return 400
    if val_errors:
        messages, fields = zip(*val_errors)
        raise errors.get_validation_error(messages, fields)

    # Collect files, drop duplicates
    file_ids = set(request.openapi_validated.body['fileIds'])
    db_files = { file_id : resource.resource_query_by_id(db, File, file_id).options(joinedload(File.metadatumrecord)).one_or_none() for file_id in file_ids }

    # Validate submission access to the specified files
    validation.validate_submission_access(db, db_files, {}, auth_user)

    # Validate the provided records
    validate_metadataset_record(service_metadata, records, return_err_message=False, rendered=False)

    # Update the metadatum records
    records = render_record_values(service_metadata, records)
    for record_name, record_value in records.items():
        db_rec = service_records[record_name]
        db_rec.value = record_value
        db.add(db_rec)

    # Validate the associations between files and records
    fnames, ref_fnames, val_errors = validation.validate_submission_association(db_files, { metadataset.site_id : metadataset }, ignore_submitted_metadatasets=True)

    # If there were any validation errors, return 400
    if val_errors:
        entities, fields, messages = zip(*val_errors)
        raise errors.get_validation_error(messages=messages, fields=fields, entities=entities)

    # Given that validation hasn't failed, we know that file names are unique. Flatten the dict.
    fnames = { k : v[0] for k, v in fnames.items() }

    # Associate the files with the metadata
    for fname, mdatrec in ref_fnames.items():
        mdatrec.file = fnames[fname]
        db.add(mdatrec)

    # Create a service execution
    sexec = ServiceExecution(
            service       = service,
            metadataset   = metadataset,
            user          = auth_user,
            datetime      = datetime.datetime.utcnow()
            )

    db.add(sexec)

    # Check which metadata of this metadataset the user is allowed to view
    metadata_with_access = get_metadata_with_access(db, auth_user)

    return MetaDataSetResponse.from_metadataset(metadataset, metadata_with_access)
