# Copyright (c) 2021 Leon Kuchenbecker <leon.kuchenbecker@uni-tuebingen.de>
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

from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config

import datameta

import bcrypt

from datameta.models import User, Group

from .. import security

@view_config(route_name='admin', renderer='../templates/admin.pt')
def v_admin(request):
    security.require_admin(request)
    return {}

@view_config(route_name='admin_json', renderer='json')
def v_admin_json(request):
    if not security.admin_logged_in(request):
        return {}

    users = [ {
        'id' : user.id,
        'group_id' : user.group.id,
        'group_name' : user.group.name,
        'fullname' : user.fullname,
        'email' : user.email
        } for user in request.dbsession.query(User).all() ]

    groups = [ { k : v for k,v in group.__dict__.items() if k in ['id','name'] } for group in request.dbsession.query(Group).all() ]

    return {
            'users' : users,
            'groups' : groups
            }

