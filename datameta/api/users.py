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


from typing import Optional

from pyramid.view import view_config
from pyramid.request import Request
from pyramid.httpexceptions import HTTPNoContent, HTTPForbidden, HTTPNotFound

from dataclasses import dataclass
from . import DataHolderBase
from ..models import User, Group
from .. import security
from ..security import authz
from ..resource import resource_by_id, get_identifier


@dataclass
class UserUpdateRequest(DataHolderBase):
    """Class for User Update Request communication to OpenApi"""
    name: str
    groupId: str
    groupAdmin: bool
    siteAdmin: bool
    enabled: bool
    siteRead: bool


@dataclass
class UserResponseElement(DataHolderBase):
    """Class for User Update Request communication to OpenApi"""
    id: dict
    name: str  # why is this name when it is called fullname in the db?
    group_id: dict
    group_admin: Optional[bool] = None
    site_admin: Optional[bool] = None
    site_read: Optional[bool] = None
    email: Optional[str] = None

    @classmethod
    def from_user(cls, target_user, requesting_user):
        restricted_fields = dict()

        if authz.view_restricted_user_info(requesting_user, target_user):
            restricted_fields.update({
                "group_admin": target_user.group_admin,
                "site_admin": target_user.site_admin,
                "site_read": target_user.site_read,
                "email": target_user.email
            })

        return cls(id=get_identifier(target_user), name=target_user.fullname, group_id=get_identifier(target_user.group), **restricted_fields)


@dataclass
class WhoamiResponseElement(DataHolderBase):
    """Class for User Update Request communication to OpenApi"""
    id: dict
    name: str  # why is this name when it is called fullname in the db?
    group_admin: bool
    site_admin: bool
    site_read: bool
    email: str
    group: dict


@view_config(
    route_name="rpc_whoami",
    renderer='json',
    request_method="GET",
    openapi=True
)
def get_whoami(request: Request) -> WhoamiResponseElement:

    auth_user = security.revalidate_user(request)

    return WhoamiResponseElement(
        id              =   get_identifier(auth_user),
        name            =   auth_user.fullname,
        group_admin     =   auth_user.group_admin,
        site_admin      =   auth_user.site_admin,
        site_read       =   auth_user.site_read,
        email           =   auth_user.email,
        group           =   {"id": get_identifier(auth_user.group), "name": auth_user.group.name}
    )


@view_config(
    route_name="user_id",
    renderer="json",
    request_method="GET",
    openapi=True
)
def get(request: Request):

    # Authenticate the user
    auth_user = security.revalidate_user(request)

    user_id = request.matchdict["id"]
    db = request.dbsession

    # Get the targeted user
    target_user = resource_by_id(db, User, user_id)
    if target_user is None:
        raise HTTPNotFound()

    if not authz.view_user(auth_user, target_user):
        raise HTTPForbidden()

    return UserResponseElement.from_user(target_user, auth_user)


@view_config(
    route_name="user_id",
    renderer='json',
    request_method="PUT",
    openapi=True
)
def put(request: Request):
    """Change user properties"""

    user_id = request.matchdict["id"]
    name = request.openapi_validated.body.get("name")
    group_id = request.openapi_validated.body.get("groupId")
    group_admin = request.openapi_validated.body.get("groupAdmin")
    site_admin = request.openapi_validated.body.get("siteAdmin")
    enabled = request.openapi_validated.body.get("enabled")
    site_read = request.openapi_validated.body.get("siteRead")

    db = request.dbsession

    # Authenticate the user
    auth_user = security.revalidate_user(request)

    # Get the targeted user
    target_user = resource_by_id(db, User, user_id)

    if target_user is None:
        raise HTTPNotFound()  # 404 User ID not found

    # First, check, if the user has the rights to perform all the changes they want

    # The user has to be site admin to change another users group
    if group_id and not authz.update_user_group(auth_user):
        raise HTTPForbidden()

    # The user has to be site admin to change site_read permissions for a user
    if site_read is not None and not authz.update_user_siteread(auth_user):
        raise HTTPForbidden()

    # The user has to be site admin to make another user site admin
    if site_admin is not None and not authz.update_user_siteadmin(auth_user, target_user):
        raise HTTPForbidden()

    # The user has to be site admin or group admin of the users group to make another user group admin
    if group_admin is not None and not authz.update_user_groupadmin(auth_user, target_user):
        raise HTTPForbidden()

    # The user has to be site admin or group admin of the users group to enable or disable a user
    if enabled is not None and not authz.update_user_status(auth_user, target_user):
        raise HTTPForbidden()

    # The user can change their own name or be site admin or group admin of the users group to change the name of another user
    if name is not None and not authz.update_user_name(auth_user, target_user):
        raise HTTPForbidden()

    # Now, make the corresponding changes
    if group_id is not None:
        new_group = resource_by_id(db, Group, group_id)
        if new_group is None:
            raise HTTPNotFound()  # 404 Group ID not found
        target_user.group_id = new_group.id
    if site_read is not None:
        target_user.site_read = site_read
    if site_admin is not None:
        target_user.site_admin = site_admin
    if group_admin is not None:
        target_user.group_admin = group_admin
    if enabled is not None:
        target_user.enabled = enabled
    if name is not None:
        target_user.fullname = name

    return HTTPNoContent()
