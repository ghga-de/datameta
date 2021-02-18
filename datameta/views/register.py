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

from ..models import User, Group, RegRequest

import logging
log = logging.getLogger(__name__)

import re

@view_config(route_name='register_submit', renderer='json')
def v_register_submit(request):
    try:
        errors = {}
        name = request.POST['name']
        email = request.POST['email']
        org_select = int(request.POST['org_select'])
        org_create = request.POST.get('org_create') is not None
        org_new_name = request.POST.get('org_new_name')

        # Basic validity check for email
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            errors['email'] = True
        else:
            # Check if the user already exists
            if request.dbsession.query(User).filter(User.email==email).one_or_none() is not None:
                errors['user_exists'] = True
            elif request.dbsession.query(RegRequest).filter(RegRequest.email==email).one_or_none() is not None:
                errors['req_exists'] = True

        # Check whether the selected organization is valid
        if org_create:
            if not org_new_name:
                errors["org_new_name"] = True
        else:
            group = request.dbsession.query(Group).filter(Group.id==org_select).one_or_none()
            if group is None:
                errors['org_select'] = True

        # Check whether a name was specified
        if not name:
            errors['name'] = True

        # If errors occurred, return them
        if errors:
            return { 'success' : False, 'errors' : errors }

        # Store a new registration request in the database
        reg_req = RegRequest(
                fullname = name,
                email = email,
                group_id = None if org_create else group.id,
                new_group_name = None if not org_create else org_new_name
                )
        request.dbsession.add(reg_req)

        if org_create:
            log.info(f"REGISTRATION REQUEST [email='{email}', name='{name}', new_org='{org_new_name}']")
        else:
            log.info(f"REGISTRATION REQUEST [email='{email}', name='{name}', group='{group.name}']")

        return { 'success' : True }
    except (ValueError, KeyError):
        pass

    return { 'success' : False }

@view_config(route_name='register', renderer='../templates/register.pt')
def v_register(request):
    groups = request.dbsession.query(Group).all()
    return {
            'pagetitle' : 'DataMeta - Registration',
            'groups' : [ {'id' : g.id, 'name' : g.name} for g in groups ]
            }
