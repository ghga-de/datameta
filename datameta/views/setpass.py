# Copyright (c) 2021 Universität Tübingen, Germany
# Authors: Leon Kuchenbecker <leon.kuchenbecker@uni-tuebingen.de>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell # copies of the Software, and to permit persons to whom the Software is
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

from pyramid.httpexceptions import HTTPFound, HTTPNoContent, HTTPBadRequest, HTTPUnauthorized
from pyramid.view import view_config

from ..models import User, PasswordToken
from .. import security
from .forgot import send_forgot_token

import datetime
import logging
log = logging.getLogger(__name__)

import re

@view_config(route_name='updatepass_api', renderer='json')
def v_updatepass_api(request):
    user = security.revalidate_user(request)

    # Try to extract old and new password from request
    try:
        old_password = request.json_body["old_password"]
        new_password = request.json_body["new_password"]
    except Error:
        raise HTTPBadRequest(json_body={'reason' : 'missing field'})

    # Validate old password
    if not security.check_password_by_hash(old_password, user.pwhash):
        raise HTTPUnauthorized()

    # Validate password
    if len(new_password) < 10:
        raise HTTPBadRequest(json_body={'reason' : 'password too short'})

    # Set the new password
    user.pwhash = security.hash_password(new_password)

    return { 'success' : True }


@view_config(route_name='setpass_api', renderer='json')
def v_setpass_api(request):
    # Invalidate the session if there was any user logged in
    request.session.invalidate()

    # Extract data from the request
    try:
        newpass = request.json_body["new_password"]
        token   = request.json_body["token"]
    except KeyError:
        return { 'success' : False, 'error' : 'INVALID_REQUEST' }

    # Validate token
    dbtoken = request.dbsession.query(PasswordToken).filter(PasswordToken.value==token).one_or_none()
    if dbtoken is None:
        return { 'success' : False, 'error' : 'TOKEN_NOT_FOUND'}
    if dbtoken.expires < datetime.datetime.now():
        return { 'success' : False, 'error' : 'TOKEN_EXPIRED' }

    # Validate password
    if len(newpass) < 10:
        return { "success" : False, "error" : "CUSTOM" , "error_msg" : "Please specify a password of at least 10 characters" }

    # Set password
    dbtoken.user.pwhash = security.hash_password(newpass)

    # Delete the token
    request.dbsession.delete(dbtoken)

    return { 'success' : True }

@view_config(route_name='setpass', renderer='../templates/setpass.pt')
def v_setpass(request):
    # Validate token
    dbtoken = request.dbsession.query(PasswordToken).filter(PasswordToken.value==request.matchdict['token']).one_or_none()
    unknown_token = dbtoken is None
    expired_token = dbtoken is not None and dbtoken.expires < datetime.datetime.now()

    # Token expired? Send new one.
    if expired_token:
        send_forgot_token(request, dbtoken.user)

    return {
            'pagetitle' : 'DataMeta - Set Password',
            'unknown_token' : unknown_token,
            'expired_token' : expired_token,
            'token_ok' : not unknown_token and not expired_token,
            'token' : request.matchdict['token']
            }
