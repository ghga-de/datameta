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

from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config

from ..models import User, PasswordToken
from .. import email, security
from ..settings import get_setting

import logging
log = logging.getLogger(__name__)

import re

def send_forgot_token(request, token):
    """Sends a password reset token email to the corresponding user"""
    db = request.dbsession

    email.send(
        recipients = (token.user.fullname, token.user.email),
        subject = get_setting(db, "subject_forgot_token").str_value,
        template = get_setting(db, "template_forgot_token").str_value,
        values={
           'fullname' : token.user.fullname,
           'token_url' : request.route_url('setpass', token = token.value)
           }
        )

@view_config(route_name='forgot_api', renderer='json')
def v_forgot_api(request):
    db = request.dbsession
    # Extract email from body
    try:
        req_email = request.json_body['email']
        req_email = req_email.lower() # Convert separately to maintain KeyError
    except KeyError:
        return { 'success' : False, 'error' : 'INVALID_REQUEST' }

    if not re.match(r"[^@]+@[^@]+\.[^@]+", req_email):
        return { 'success' : False, 'error' : 'MALFORMED_EMAIL' }

    token = security.get_new_password_reset_token_from_email(db, req_email)

    # Generate a new forgot token and send it to the user
    if token:
        send_forgot_token(request, token)
        log.debug(f"USER REQUESTED RECOVERY TOKEN: {token.value}")

    return { 'success' : True }

@view_config(route_name='forgot', renderer='../templates/forgot.pt')
def v_forgot(request):
    # Invalidate this session
    request.session.invalidate()

    return {
            'pagetitle' : 'DataMeta - Recover Password',
            }
