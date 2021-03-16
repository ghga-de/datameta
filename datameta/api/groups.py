# Copyright (c) 2021 Universität Tübingen, Germany
# Authors: Leon Kuchenbecker <leon.kuchenbecker@uni-tuebingen.de>,
#          Kersten Breuer <k.breuer@dkfz.de>
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
def get(request: Request) -> ChangeGroupName:
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