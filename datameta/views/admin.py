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

from pyramid.httpexceptions import HTTPFound, HTTPBadRequest, HTTPNotFound, HTTPUnauthorized, HTTPNoContent, HTTPForbidden
from pyramid.view import view_config

import bcrypt

from ..models import User, Group, RegRequest
from ..settings import get_setting
from .. import email, passtokens, security, siteid

import logging
log = logging.getLogger(__name__)

@view_config(route_name='admin', renderer='../templates/admin.pt')
def v_admin(request):
    security.revalidate_admin(request)
    try:
	    return { 'showreq' : request.GET['showreq'] }
    except KeyError:
	    return { 'showreq' : '' }

@view_config(route_name='admin_put_request', renderer='json', request_method='PUT')
def v_admin_put_request(request):
    """Serves PUT requests at /api/admin/request that allows the user to
    respond to registration requests that were made againts the site and for
    which the user is authorative."""

    # Make sure an admin is logged in
    req_user = security.revalidate_admin(request)

    db = request.dbsession

    # Parse request
    accept = False
    try:
        reg_req_id             = request.json_body['id']
        response               = request.json_body['response']
        newuser_make_admin     = bool(request.json_body.get("group_admin"))
        newuser_fullname       = request.json_body['fullname'] # Admin can edit upon confirm
        newuser_group_id       = request.json_body['group_id'] if request.json_body['group_id'] is not None else None # Admin can edit upon confirm
        newuser_group_newname  = request.json_body['group_newname'] # Admin can edit upon confirm
        if response.lower() == 'accept':
            accept = True
        elif response.lower() == 'reject':
            accept = False
        else:
            raise SyntaxError()
    except Exception as e:
        log.error(f"MALFORMED API REQUEST AT /api/admin/request: {e}")
        raise HTTPBadRequest()

    # Check if the request exists
    reg_req = db.query(RegRequest).filter(RegRequest.uuid==reg_req_id).one_or_none()
    if reg_req is None:
        return HTTPNotFound('Registration request not found')

    # Check if the requesting user is authorized. Both the request group as well as the
    # administratively selected group have to be the requesting user's group
    if not req_user.site_admin and (reg_req.group_id!=req_user.group_id.uuid or newuser_group_id!=req_user.group_id.uuid):
        return HTTPUnauthorized()

    # Check if the specified group id is valid
    db_group = db.query(Group).filter(Group.uuid==newuser_group_id).one_or_none() if newuser_group_id is not None else None
    if newuser_group_id is not None and not db_group:
        return HTTPNoContent('Group not found')

    # Implemented the requested response to the user registration request
    if accept:
        # Create user and group
        group = db_group if newuser_group_id is not None else Group(name=newuser_group_newname, site_id=siteid.generate(request, Group))

        new_user = User(
                fullname = newuser_fullname,
                site_id = siteid.generate(request, User),
                email = reg_req.email,
                group = group,
                enabled = True,
                site_admin = False,
                group_admin = newuser_make_admin,
                pwhash = '!')

        db.add(new_user)
        db.flush() # We need an ID

        # Delete the request
        db.delete(reg_req)

        # Obtain a new token
        token = passtokens.new_token(db, new_user.id)

        # Generate the token url
        token_url = request.route_url('setpass', token = token)

        # Send the token to the user
        email.send(
                recipients = (new_user.fullname, new_user.email),
                subject = get_setting(db, "subject_welcome_token").str_value,
                template = get_setting(db, "template_welcome_token").str_value,
                values={
                    'fullname' : new_user.fullname,
                    'token_url' : token_url
                    }
                )
        log.info(f"NEW USER '{new_user.email}' [GROUP '{new_user.group.name}'] CONFIRMED BY '{req_user.email}'")
    else:
        # Denote email and name before request deletion
        reg_req_email = reg_req.email
        reg_req_fullname = reg_req.fullname

        # Delete the request
        db.delete(reg_req)

        # Inform the user
        email.send(
                recipients = (reg_req_fullname, reg_req_email),
                subject = get_setting(db, "subject_reject").str_value,
                template = get_setting(db, "template_reject").str_value,
                values={
                    'fullname' : reg_req_fullname,
                    }
                )
        log.info(f"REGISTRATION REQUEST BY '{reg_req_email}' REJECTED BY '{req_user.email}'")

    return HTTPNoContent()


@view_config(route_name='admin_get', renderer='json', request_method='GET')
def v_admin_get(request):
    """Serves GET requests made against /admin to render the admin view"""
    # Make sure an admin is logged in
    req_user = security.revalidate_admin(request)

    db = request.dbsession

    query = db.query(User)

    # If the requesting user is only a group admin, return only those users
    # that are in the same group
    if not req_user.site_admin:
        query = query.filter(User.group_id==req_user.group_id)

    response = {}

    response["users"] = [ {
        'id' : {'uuid' : str(user.uuid), 'site_id' : user.site_id},
        'group_id' : {'uuid' : str(user.group.uuid), 'site_id' : user.group.site_id},
        'group_name' : user.group.name,
        'fullname' : user.fullname,
        'email' : user.email,
        'enabled' : user.enabled,
        'site_admin' : user.site_admin,
        'group_admin' : user.group_admin
        } for user in query ]

    # If the requesting user is a site admin, return all groups, otherwise only theirs
    if req_user.site_admin:
        response['groups'] = [ { 
            'id' : {'uuid': str(group.uuid), 'site' : group.site_id },
            'name': group.name
            } for group in db.query(Group) ]
    else:
        response['groups'] = [ { 
            'id' : {'uuid': str(group.uuid), 'site' : group.site_id },
            'name': group.name
            } for group in [ req_user.group ] ]
    # Pending registration requests
    query = db.query(RegRequest)
    if not req_user.site_admin:
        query = query.filter(RegRequest.group_id==req_user.group_id)

    response['reg_requests'] = [ { 
        'id' : str(reg_request.uuid),
        'fullname' : reg_request.fullname, 
        'email' : reg_request.email, 
        'group_id': ( str(reg_request.group.uuid) if reg_request.group else None),
        'new_group_name' : reg_request.new_group_name
        } for reg_request in query ] 

    return response
