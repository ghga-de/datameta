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
from ..resource import resource_by_id
from pyramid.httpexceptions import HTTPNoContent, HTTPForbidden



@dataclass
class MetaDataResponseElement(DataHolderBase):
    """MetaDataSetResponse container for OpenApi communication"""
    id                      :  dict
    name                    :  str
    is_mandatory            :  bool
    order                   :  int
    is_file                 :  bool
    is_submission_unique    :  bool
    is_site_unique          :  bool
    regex_description       :  Optional[str] = None
    long_description        :  Optional[str] = None
    reg_exp                 :  Optional[str] = None
    date_time_fmt           :  Optional[str] = None

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
                regex_description     =  metadatum.short_description,
                long_description      =  metadatum.long_description,
                reg_exp               =  metadatum.regexp,
                date_time_fmt         =  metadatum.datetimefmt,
                is_mandatory          =  metadatum.mandatory,
                order                 =  metadatum.order,
                is_file               =  metadatum.isfile,
                is_submission_unique  =  metadatum.submission_unique,
                is_site_unique        =  metadatum.site_unique
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

    target_metadatum = MetaDatum(
        name = request.openapi_validated.body["name"],
        short_description = request.openapi_validated.body["regex_description"],
        long_description = request.openapi_validated.body["long_description"],
        regexp = request.openapi_validated.body["reg_exp"],
        datetimefmt = request.openapi_validated.body["date_time_fmt"],
        mandatory = request.openapi_validated.body["is_mandatory"],
        order = request.openapi_validated.body["order"],
        isfile = request.openapi_validated.body["is_file"],
        submission_unique = request.openapi_validated.body["is_submission_unique"],
        site_unique = request.openapi_validated.body["is_site_unique"]
    )

    target_metadatum.name = "name"

    return HTTPNoContent()


@view_config(
    route_name="metadata_id",
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

    metadata = MetaDatum(
        name = request.openapi_validated.body["name"],
        short_description = request.openapi_validated.body["regex_description"],
        long_description = request.openapi_validated.body["long_description"],
        regexp = request.openapi_validated.body["reg_exp"],
        datetimefmt = request.openapi_validated.body["date_time_fmt"],
        mandatory = request.openapi_validated.body["is_mandatory"],
        order = request.openapi_validated.body["order"],
        isfile = request.openapi_validated.body["is_file"],
        submission_unique = request.openapi_validated.body["is_submission_unique"],
        site_unique = request.openapi_validated.body["is_site_unique"]
    )

    db.add(metadata)
    db.flush()

    raise HTTPNoContent
