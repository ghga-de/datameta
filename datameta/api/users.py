# Copyright (c) 2021 Universität Tübingen, Germany
# Authors: Leon Kuchenbecker <leon.kuchenbecker@uni-tuebingen.de>,
#          Moritz Hahn <moritz.hahn@uni-tuebingen.de>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from pyramid.view import view_config
from pyramid.request import Request
from pyramid.httpexceptions import HTTPNoContent, HTTPForbidden, HTTPBadRequest

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
def get(request: Request) -> UserUpdateRequest:
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
        raise HTTPForbidden() # 403 User ID not found

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
        if not (auth_user.site_admin or auth_user.group_admin and auth_user.group.uuid == target_user.group.uuid):
            raise HTTPForbidden()

    # The user has to be site admin or group admin of the users group to enable or disable a user
    if enabled != None:
        if not (auth_user.site_admin or auth_user.group_admin and auth_user.group.uuid == target_user.group.uuid):
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
            raise HTTPForbidden() # 403 Group ID not found
        target_user.group.id = new_group.id
    if site_admin != None:
        target_user.site_admin = site_admin
    if group_admin != None:
        target_user.group_admin = group_admin
    if enabled != None:
        target_user.enabled = enabled
    if name != None:
        target_user.fullname = name

    return HTTPNoContent()
