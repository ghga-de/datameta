# Copyright 2021 Universität Tübingen
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

from dataclasses import dataclass
from pyramid.httpexceptions import HTTPForbidden, HTTPNotFound, HTTPNoContent
from pyramid.view import view_config
from pyramid.request import Request
from typing import Optional, Dict
from ..linting import validate_metadataset_record
from .. import security, siteid, models
import datetime
from ..resource import resource_by_id, get_identifier
from . import DataHolderBase
from .. import errors

@dataclass
class MetaDataSetResponse(DataHolderBase):
    """MetaDataSetResponse container for OpenApi communication"""
    id: dict
    record: dict
    group_id: str
    user_id: str
    submission_id: Optional[str] = None

def render_record_values(mdatum:Dict[str, models.MetaDatum], record:dict) -> dict:
    """Renders values of a metadataset record. Please note: the record should already have passed validation."""
    record_rendered = record.copy()
    for field in mdatum:
        if not field in record_rendered.keys():
            # if field is not contained in record, add it as None to the record:
            record_rendered[field] = None
            continue
        elif field is None:
            continue
        elif mdatum[field].datetimefmt:
            # if MetaDatum is a datetime field, render the value in isoformat
            record_rendered[field] = datetime.datetime.strptime(
                    record_rendered[field],
                    mdatum[field].datetimefmt
                ).isoformat()

    return record_rendered

def formatted_mrec_value(mrec):
    if mrec.metadatum.datetimefmt is not None:
        return datetime.datetime.fromisoformat(mrec.value).strftime(mrec.metadatum.datetimefmt)
    else:
        return mrec.value

def get_record_from_metadataset(mdata_set:models.MetaDataSet) -> dict:
    """ Construct a dict containing all records of that MetaDataSet"""
    return {
        rec.metadatum.name: formatted_mrec_value(rec)
        for rec in mdata_set.metadatumrecords
    }

@view_config(
    route_name="metadatasets",
    renderer='json',
    request_method="POST",
    openapi=True
)
def post(request:Request) -> MetaDataSetResponse:
    """Create new metadataset"""
    auth_user = security.revalidate_user(request)
    record = request.openapi_validated.body["record"]
    # prevalidate (raises 400 in case of validation failure):
    validate_metadataset_record(request, record)

    # render records according to MetaDatum constraints
    db = request.dbsession
    mdatum_query = db.query(models.MetaDatum).order_by(
        models.MetaDatum.order
    ).all()
    mdatum = {mdat.name: mdat for mdat in mdatum_query }
    record = render_record_values(mdatum, record)

    # construct new MetaDataSet:
    mdata_set = models.MetaDataSet(
        site_id = siteid.generate(request, models.MetaDataSet),
        user_id = auth_user.id,
        group_id = auth_user.group.id,
        submission_id = None
    )
    db.add(mdata_set)
    db.flush()

    # construct new MetaDatumRecords
    for name, value in record.items():
        mdatum_rec = models.MetaDatumRecord(
            metadatum_id = mdatum[name].id,
            metadataset_id = mdata_set.id,
            file_id = None,
            value = value
        )
        db.add(mdatum_rec)

    return MetaDataSetResponse(
        id             = get_identifier(mdata_set),
        record         = record,
        group_id       = get_identifier(mdata_set.group),
        user_id        = get_identifier(mdata_set.user),
        submission_id  = get_identifier(mdata_set.submission) if mdata_set.submission else None,
    )


@view_config(
    route_name="metadatasets_id",
    renderer='json',
    request_method="GET",
    openapi=True
)
def get_metadataset(request:Request) -> MetaDataSetResponse:
    """Create new metadataset"""
    auth_user = security.revalidate_user(request)
    db = request.dbsession
    mdata_set = resource_by_id(db, models.MetaDataSet, request.matchdict['id'])

    if not mdata_set:
        raise HTTPNotFound()

    # check if user is in the group of that metadataset:
    if not auth_user.group.id == mdata_set.group.id:
        raise HTTPForbidden()

    return MetaDataSetResponse(
        id=get_identifier(mdata_set),
        record=get_record_from_metadataset(mdata_set),
        group_id=get_identifier(mdata_set.group),
        user_id=get_identifier(mdata_set.user),
        submission_id=get_identifier(mdata_set.submission) if mdata_set.submission else None,
    )

@view_config(
    route_name="metadatasets_id",
    renderer='json',
    request_method="DELETE",
    openapi=True
)
def delete_metadataset(request:Request) -> HTTPNoContent:
    # Check authentication or raise 401
    auth_user = security.revalidate_user(request)

    db = request.dbsession

    # Find the requested metadataset
    mdata_set = resource_by_id(db, models.MetaDataSet, request.matchdict['id'])

    # Check if the metadataset exists
    if not mdata_set:
        raise HTTPNotFound()

    # Check if user owns this metadataset
    if auth_user.group.id != mdata_set.group.id or auth_user.id != mdata_set.user_id:
        raise HTTPForbidden()

    # Check if the metadataset was already submitted
    if mdata_set.submission:
        raise errors.get_not_modifiable_error()

    # Delete the records
    request.dbsession.query(models.MetaDatumRecord).filter(models.MetaDatumRecord.metadataset_id==mdata_set.id).delete()

    # Delete the metadataset
    db.delete(mdata_set)

    return HTTPNoContent()
