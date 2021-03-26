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

from pyramid.view import view_config
from pyramid.request import Request
from typing import Optional, Dict, List
from dataclasses import dataclass
from . import DataHolderBase
from .. import models
from ..models import Group
from .. import security, errors
from ..resource import resource_by_id

from pyramid.httpexceptions import HTTPNoContent, HTTPNotFound, HTTPForbidden, HTTPBadRequest, HTTPGone


class GroupSubmissions:
    """GroupSubmissions container for OpenApi communication"""
    submissions: List[dict]

    def __init__(self, request:Request, group_id:str):
        db = request.dbsession
        # To Developer:
        # Please insert code that queries the db
        # for all submissions for the given group_id
        # and store that list in self.submissions


    def __json__(self) -> List[dict]:
        return self(submissions)


@view_config(
    route_name="groups_id_submissions",
    renderer='json',
    request_method="GET",
    openapi=True
)
def get(request: Request) -> GroupSubmissions:
    """Get all submissions of a given group."""
    pass
    return {}

@dataclass
class ChangeGroupName(DataHolderBase):
    """Class for Group Name Change communication to OpenApi"""
    group_id: str
    new_group_name: str

@view_config(
    route_name="groups_id", 
    renderer='json', 
    request_method="PUT", 
    openapi=True
)
def put(request: Request):
    """Change the name of the group"""

    group_id = request.matchdict["id"]
    newGroupName = request.openapi_validated.body["name"]
    db = request.dbsession

    # Authenticate the user
    auth_user = security.revalidate_user(request)

    target_group = resource_by_id(db, Group, group_id)

    if target_group is None:
        raise HTTPForbidden() # 403 Group ID not found, hidden from the user intentionally

    # Change the group name only if the user is site admin or the admin for the specific group
    if auth_user.site_admin or auth_user.group_admin and auth_user.group.uuid == group_id:
        target_group.name = newGroupName
        return HTTPNoContent()
    
    raise HTTPForbidden() # 403 Not authorized to change this group name
