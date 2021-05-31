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

from dataclasses import dataclass
from typing import Optional, List
from pyramid.request import Request
from pyramid.view import view_config
from . import DataHolderBase
from ..models import MetaDatum, User, Service, MetaDataSet, MetaDatumRecord
from .. import resource, security
from ..security import authz
from ..resource import resource_by_id, get_identifier
from pyramid.httpexceptions import HTTPForbidden, HTTPNotFound
from sqlalchemy.orm import joinedload


def get_all_metadata(db, include_service_metadata = True):
    """Queries all metadata that are currently defined and returns the database
    objects as a dictionary with the metadata names as keys.

    Arguments:
        include_service_metadata - If true, include metadata with a service reference,
        otherwise exclude those
    """
    q = db.query(MetaDatum)
    if not include_service_metadata:
        q = q.filter(MetaDatum.service_id.is_(None))
    return { mdata.name : mdata for mdata in q }


def get_service_metadata(db):
    """Queries all metadata that are currently defined and are service
    metadata."""
    return { mdata.name : mdata for mdata in db.query(MetaDatum).filter(MetaDatum.service_id.isnot(None)) }


def get_metadata_with_access(db, user: User):
    """Queries all metadata that are currently defined and reduces the set
    according to the specified user's data access rights"""
    all_metadata = get_all_metadata(db, include_service_metadata = True)
    return authz.get_readable_metadata(all_metadata, user)


@dataclass
class MetaDataResponseElement(DataHolderBase):
    """MetaDataSetResponse container for OpenApi communication"""
    id                      : dict
    name                    : str
    is_mandatory            : bool
    order                   : int
    is_file                 : bool
    is_submission_unique    : bool
    is_site_unique          : bool
    regex_description       : Optional[str] = None
    long_description        : Optional[str] = None
    example                 : Optional[str] = None
    reg_exp                 : Optional[str] = None
    date_time_fmt           : Optional[str] = None
    service_id              : Optional[dict] = None


@view_config(
    route_name="metadata",
    renderer='json',
    request_method="GET",
    openapi=True
)
def get(request: Request) -> List[MetaDataResponseElement]:
    """Obtain information for all metadata that are currently configured."""
    security.revalidate_user(request)

    metadata = request.dbsession.query(MetaDatum).order_by(MetaDatum.order).options(joinedload(MetaDatum.service))

    return [
        MetaDataResponseElement(
            id                    =  resource.get_identifier(metadatum),
            name                  =  metadatum.name,
            regex_description     =  metadatum.short_description,
            long_description      =  metadatum.long_description,
            example               =  metadatum.example,
            reg_exp               =  metadatum.regexp,
            date_time_fmt         =  metadatum.datetimefmt,
            is_mandatory          =  metadatum.mandatory,
            order                 =  metadatum.order,
            is_file               =  metadatum.isfile,
            is_submission_unique  =  metadatum.submission_unique,
            is_site_unique        =  metadatum.site_unique,
            service_id            =  None if not metadatum.service else get_identifier(metadatum.service)
            )
        for metadatum in metadata
        ]


@view_config(
    route_name="metadata_id",
    renderer='json',
    request_method="PUT",
    openapi=True
)
def put(request: Request) -> MetaDataResponseElement:
    """Change a metadatum"""
    auth_user = security.revalidate_user(request)
    metadata_id = request.matchdict["id"]

    # Only site admins can change metadata
    if not authz.update_metadatum(auth_user):
        raise HTTPForbidden()

    body = request.openapi_validated.body
    db = request.dbsession
    target_metadatum = resource_by_id(db, MetaDatum, metadata_id)

    target_metadatum.name                = body["name"]
    target_metadatum.short_description   = body["regexDescription"] if body["regexDescription"] else None
    target_metadatum.long_description    = body["longDescription"] if body["longDescription"] else None
    target_metadatum.example             = body["example"]
    target_metadatum.regexp              = body["regExp"] if body["regExp"] else None
    target_metadatum.datetimefmt         = body["dateTimeFmt"] if body["dateTimeFmt"] else None
    target_metadatum.mandatory           = body["isMandatory"]
    target_metadatum.order               = body["order"]
    target_metadatum.isfile              = body["isFile"]
    target_metadatum.submission_unique   = body["isSubmissionUnique"]
    target_metadatum.site_unique         = body["isSiteUnique"]

    service_id = body["serviceId"]
    if service_id:
        service = resource_by_id(db, Service, service_id)
        if service is not None:
            target_metadatum.service_id = service.id
        else:
            raise HTTPNotFound()  # 404 Service ID not found
    else:
        target_metadatum.service_id = None

    return MetaDataResponseElement(
        id                    =  resource.get_identifier(target_metadatum),
        name                  =  target_metadatum.name,
        regex_description     =  target_metadatum.short_description,
        long_description      =  target_metadatum.long_description,
        example               =  target_metadatum.example,
        reg_exp               =  target_metadatum.regexp,
        date_time_fmt         =  target_metadatum.datetimefmt,
        is_mandatory          =  target_metadatum.mandatory,
        order                 =  target_metadatum.order,
        is_file               =  target_metadatum.isfile,
        is_submission_unique  =  target_metadatum.submission_unique,
        is_site_unique        =  target_metadatum.site_unique,
        service_id            =  None if not target_metadatum.service else get_identifier(target_metadatum.service)
    )


@view_config(
    route_name="metadata",
    renderer='json',
    request_method="POST",
    openapi=True
)
def post(request: Request) -> MetaDataResponseElement:
    """POST a new metadatum"""
    auth_user = security.revalidate_user(request)

    # Only site admins can post new metadata
    if not authz.create_metadatum(auth_user):
        raise HTTPForbidden()

    body = request.openapi_validated.body
    db = request.dbsession
    service = resource_by_id(db, Service, body["serviceId"])

    metadatum = MetaDatum(
        name                = body["name"],
        short_description   = body["regexDescription"] if body["regexDescription"] else None,
        long_description    = body["longDescription"] if body["longDescription"] else None,
        example             = body["example"],
        regexp              = body["regExp"] if body["regExp"] else None,
        datetimefmt         = body["dateTimeFmt"] if body["dateTimeFmt"] else None,
        mandatory           = body["isMandatory"],
        order               = body["order"],
        isfile              = body["isFile"],
        submission_unique   = body["isSubmissionUnique"],
        site_unique         = body["isSiteUnique"],
        service_id          = None if not service else service.id
    )

    db.add(metadatum)

    # Add a NULL value for every metadataset
    db.add_all(MetaDatumRecord(metadataset_id=mset_id, metadatum=metadatum) for (mset_id,) in db.query(MetaDataSet.id))

    db.flush()

    return MetaDataResponseElement(
        id                    =  resource.get_identifier(metadatum),
        name                  =  metadatum.name,
        regex_description     =  metadatum.short_description,
        long_description      =  metadatum.long_description,
        example               =  metadatum.example,
        reg_exp               =  metadatum.regexp,
        date_time_fmt         =  metadatum.datetimefmt,
        is_mandatory          =  metadatum.mandatory,
        order                 =  metadatum.order,
        is_file               =  metadatum.isfile,
        is_submission_unique  =  metadatum.submission_unique,
        is_site_unique        =  metadatum.site_unique,
        service_id            =  None if not metadatum.service else get_identifier(metadatum.service)
    )
