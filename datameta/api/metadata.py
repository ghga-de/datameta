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
from .. import resource, security

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
