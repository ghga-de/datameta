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
from typing import Optional, List
from pyramid.request import Request
from pyramid.view import view_config
from . import DataHolderBase
from ..models import MetaDatum
from .. import resource, security, siteid
from ..resource import resource_by_id, get_identifier
from pyramid.httpexceptions import HTTPNoContent, HTTPForbidden

@dataclass
class MetaDataResponseElement(DataHolderBase):
    """MetaDataSetResponse container for OpenApi communication"""
    id                      :  dict
    name                    :  str
    isMandatory            :  bool
    order                   :  int
    isFile                 :  bool
    isSubmissionUnique    :  bool
    isSiteUnique          :  bool
    regexDescription       :  Optional[str] = None
    longDescription        :  Optional[str] = None
    example                 :  Optional[str] = None
    regExp                 :  Optional[str] = None
    dateTimeFmt           :  Optional[str] = None

@view_config(
    route_name="metadata",
    renderer='json',
    request_method="GET",
    openapi=True
)
def get(request:Request) -> List[MetaDataResponseElement]:
    """Obtain information for all metadata that are currently configured."""
    auth_user = security.revalidate_user(request)

    metadata = request.dbsession.query(MetaDatum)

    return [
        MetaDataResponseElement(
            id                    =  resource.get_identifier(metadatum),
            name                  =  metadatum.name,
            regexDescription     =  metadatum.short_description,
            longDescription      =  metadatum.long_description,
            example               =  metadatum.example,
            regExp               =  metadatum.regexp,
            dateTimeFmt         =  metadatum.datetimefmt,
            isMandatory          =  metadatum.mandatory,
            order                 =  metadatum.order,
            isFile               =  metadatum.isfile,
            isSubmissionUnique  =  metadatum.submission_unique,
            isSiteUnique        =  metadatum.site_unique
            )
        for metadatum in metadata
        ]

@view_config(
    route_name="metadata_id",
    renderer='json',
    request_method="PUT",
    openapi=True
)
def put(request:Request):
    """Change a metadataset"""
    auth_user = security.revalidate_user(request)
    db = request.dbsession
    metadata_id = request.matchdict["id"]

    # Only site admins can change metadatasets
    if not auth_user.site_admin:
         raise HTTPForbidden()

    target_metadatum = resource_by_id(db, MetaDatum, metadata_id)

    target_metadatum.name = request.openapi_validated.body["name"]
    target_metadatum.short_description = request.openapi_validated.body["regexDescription"]
    target_metadatum.long_description = request.openapi_validated.body["longDescription"]
    target_metadatum.example = request.openapi_validated.body["example"]
    target_metadatum.regexp = request.openapi_validated.body["regExp"]
    target_metadatum.datetimefmt = request.openapi_validated.body["dateTimeFmt"]
    target_metadatum.mandatory = request.openapi_validated.body["isMandatory"]
    target_metadatum.order = request.openapi_validated.body["order"]
    target_metadatum.isfile = request.openapi_validated.body["isFile"]
    target_metadatum.submission_unique = request.openapi_validated.body["isSubmissionUnique"]
    target_metadatum.site_unique = request.openapi_validated.body["isSiteUnique"]
    
    return HTTPNoContent()

@view_config(
    route_name="metadata",
    renderer='json',
    request_method="POST",
    openapi=True
)
def post(request:Request):
    """POST a new metadataset"""
    auth_user = security.revalidate_user(request)

    # Only site admins can post new metadatasets
    if not auth_user.site_admin:
         raise HTTPForbidden()

    metadatum = MetaDatum(
        name = request.openapi_validated.body["name"],
        short_description = request.openapi_validated.body["regexDescription"],
        long_description = request.openapi_validated.body["longDescription"],
        example = request.openapi_validated.body["example"],
        regexp = request.openapi_validated.body["regExp"],
        datetimefmt = request.openapi_validated.body["dateTimeFmt"],
        mandatory = request.openapi_validated.body["isMandatory"],
        order = request.openapi_validated.body["order"],
        isfile = request.openapi_validated.body["isFile"],
        submission_unique = request.openapi_validated.body["isSubmissionUnique"],
        site_unique = request.openapi_validated.body["isSiteUnique"],
    )

    db = request.dbsession
    db.add(metadatum)

    return HTTPNoContent()