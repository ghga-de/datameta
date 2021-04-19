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

from sqlalchemy import or_, and_
from pyramid.httpexceptions import HTTPFound, HTTPBadRequest
from pyramid.view import view_config
from ...resource import resource_by_id
from ...models import User, Group, RegRequest
from ... import email
from ...settings import get_setting

import logging
log = logging.getLogger(__name__)

import re

def get_authorative_admins(db, reg_request):
    """Identifies administrative users that are authorative for a given
    registration request and returns the corresponding database user objects"""
    if reg_request.group_id is None:
        return db.query(User).filter(User.site_admin==True).all()
    else:
        return db.query(User).filter(or_(
            User.site_admin==True,
            and_(User.group_admin==True, User.group_id == reg_request.group_id)
            )).all()

@view_config(route_name='register_submit', renderer='json')
def v_register_submit(request):

    db = request.dbsession
    errors = {}
    try:
        name = request.POST['name']
        req_email = request.POST['email']
        req_email = req_email.lower() # Convert separately to maintain KeyError
        org_select = request.POST['org_select']
        org_create = request.POST.get('org_create') is not None
        org_new_name = request.POST.get('org_new_name')
    except (KeyError, ValueError) as e:
        log.info(f"Malformed request at /api/ui/register: {e}")
        raise HTTPBadRequest()

    # Basic validity check for email
    if not re.match(r"[^@]+@[^@]+\.[^@]+", req_email):
        errors['email'] = True
    else:
        # Check if the user already exists
        if db.query(User).filter(User.email==req_email).one_or_none() is not None:
            errors['user_exists'] = True
        elif db.query(RegRequest).filter(RegRequest.email==req_email).one_or_none() is not None:
            errors['req_exists'] = True

    # Check whether the selected organization is valid
    group = None
    if org_create:
        if not org_new_name:
            errors["org_new_name"] = True
    else:
        group = resource_by_id(db, Group, org_select)
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
            email = req_email,
            group_id = None if org_create else group.id,
            new_group_name = None if not org_create else org_new_name
            )
    db.add(reg_req)
    db.flush()

    # Send out a notification to authorative admins
    admins = get_authorative_admins(db, reg_req)
    email.send(
            recipients = email.__smtp_from,
            subject = get_setting(db, "subject_reg_notify").str_value,
            template = get_setting(db, "template_reg_notify").str_value,
            values = {
                'req_fullname' : reg_req.fullname,
                'req_email' : reg_req.email,
                'req_group' : reg_req.new_group_name if org_create else group.name,
                'req_url' : request.route_url('admin') + f"?showreq={reg_req.uuid}"
                },
            bcc = [ admin.email for admin in admins ],
            rec_header_only=True # We're not actually sending this to the from address, just using it in the "To" header
            )

    if org_create:
        log.info(f"REGISTRATION REQUEST [email='{req_email}', name='{name}', new_org='{org_new_name}']")
    else:
        log.info(f"REGISTRATION REQUEST [email='{req_email}', name='{name}', group='{group.name}']")

    return { 'success' : True }