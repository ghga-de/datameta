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

from pyramid.view import view_config
from pyramid.request import Request
from pyramid.httpexceptions import HTTPNotFound

from dataclasses import dataclass
from ..models import Group, ApplicationSettings
from .. import resource
from . import DataHolderBase
from ..resource import resource_by_id, get_identifier

@dataclass
class RegisterOptionsResponse(DataHolderBase):
    groups: list
    user_agreement: str

@view_config(
    route_name="register_groups_and_agreement",
    renderer='json', 
    request_method="GET", 
    openapi=True
)
def get(request: Request) -> RegisterOptionsResponse:

    db = request.dbsession

    user_agreement = db.query(ApplicationSettings).filter(ApplicationSettings.key == "user_agreement")
    groups = db.query(Group)

    return RegisterOptionsResponse(
        groups = [ {"id": resource.get_identifier(group), "name": group.name} for group in groups ],
        user_agreement  = user_agreement
    )