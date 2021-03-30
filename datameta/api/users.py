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
from pyramid.httpexceptions import HTTPNoContent, HTTPForbidden, HTTPNotFound

from dataclasses import dataclass
from . import DataHolderBase
from ..models import User, Group
from .. import security, errors
from ..resource import resource_by_id

@dataclass
class UserUpdateRequest(DataHolderBase):
    """Class for User Update Request communication to OpenApi"""
    name: str
    groupId: str
    groupAdmin: bool
    siteAdmin: bool
    enabled: bool

@view_config(
    route_name="user_id", 
    renderer='json', 
    request_method="PUT", 
    openapi=True
)
def put(request: Request):
    """Change the name of the group"""

    user_id = request.matchdict["id"]
    name = request.openapi_validated.body.get("name")
    group_id = request.openapi_validated.body.get("groupId")
    group_admin = request.openapi_validated.body.get("groupAdmin")
    site_admin = request.openapi_validated.body.get("siteAdmin")
    enabled = request.openapi_validated.body.get("enabled")

    db = request.dbsession

    # Authenticate the user
    auth_user = security.revalidate_user(request)
    
    # Get the targeted user
    target_user = resource_by_id(db, User, user_id)

    if(target_user == None):
        raise HTTPNotFound() # 404 User ID not found

    # First, check, if the user has the rights to perform all the changes they want

    # The user has to be site admin to change another users group
    if group_id != None:
        if not auth_user.site_admin:
            raise HTTPForbidden()

    # The user has to be site admin to make another user site admin
    if site_admin != None:
        if not auth_user.site_admin:
            raise HTTPForbidden()

    # The user has to be site admin or group admin of the users group to make another user group admin
    if group_admin != None:
        if not (auth_user.site_admin or (auth_user.group_admin and auth_user.group.uuid == target_user.group.uuid)):
            raise HTTPForbidden()

    # The user has to be site admin or group admin of the users group to enable or disable a user
    if enabled != None:
        if not (auth_user.site_admin or (auth_user.group_admin and auth_user.group.uuid == target_user.group.uuid)):
            raise HTTPForbidden()
        if not auth_user.site_admin and target_user.group_admin
            raise HTTPForbidden()

    # The user can change their own name or be site admin or group admin of the users group to change the name of another user
    if name != None:
        if not (auth_user.site_admin or auth_user.group_admin and auth_user.group.uuid == target_user.group.uuid
            or auth_user.uuid == target_user.uuid):
            raise HTTPForbidden()

    # Now, make the corresponding changes
    if group_id != None:
        new_group = resource_by_id(db, Group, group_id)
        if new_group == None:
            raise HTTPNotFound() # 404 Group ID not found
        target_user.group_id = new_group.id
    if site_admin != None:
        target_user.site_admin = site_admin
    if group_admin != None:
        target_user.group_admin = group_admin
    if enabled != None:
        target_user.enabled = enabled
    if name != None:
        target_user.fullname = name

    return HTTPNoContent()
