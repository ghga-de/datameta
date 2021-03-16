# Copyright (c) 2021 Universität Tübingen, Germany
# Authors: Leon Kuchenbecker <leon.kuchenbecker@uni-tuebingen.de>
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

from sqlalchemy import or_, and_
from pyramid.httpexceptions import HTTPFound, HTTPBadRequest
from pyramid.view import view_config

from ..models import User, Group, RegRequest
from .. import email
from ..settings import get_setting

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
            and_(User.group_admin==True, User.group_id==reg_request.group_id)
            )).all()

@view_config(route_name='register_submit', renderer='json')
def v_register_submit(request):
    db = request.dbsession
    errors = {}
    try:
        name = request.POST['name']
        req_email = request.POST['email']
        org_select = int(request.POST['org_select'])
        org_create = request.POST.get('org_create') is not None
        org_new_name = request.POST.get('org_new_name')
    except (KeyError, ValueError) as e:
        log.info(f"Malformed request at /register/submit: {e}")
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
        group = db.query(Group).filter(Group.id==org_select).one_or_none()
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
                'req_url' : request.route_url('admin') + f"?showreq={reg_req.id}"
                },
            bcc = [ admin.email for admin in admins ],
            rec_header_only=True # We're not actually sending this to the from address, just using it in the "To" header
            )

    if org_create:
        log.info(f"REGISTRATION REQUEST [email='{req_email}', name='{name}', new_org='{org_new_name}']")
    else:
        log.info(f"REGISTRATION REQUEST [email='{req_email}', name='{name}', group='{group.name}']")

    return { 'success' : True }

@view_config(route_name='register', renderer='../templates/register.pt')
def v_register(request):
    groups = request.dbsession.query(Group).all()
    return {
            'pagetitle' : 'DataMeta - Registration',
            'groups' : [ {'id' : g.id, 'name' : g.name} for g in groups ]
            }
