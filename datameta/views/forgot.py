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
from ..security import hash_password
from .. import passtokens, email
from ..settings import get_setting

import logging
log = logging.getLogger(__name__)

import re

def send_forgot_token(request, user):
    """Generates a new set-pass token for the specified user and sends out an
    email to the user with the password recovery URL. The email templatet
    assumes a 'forgotten password' scenario."""
    db = request.dbsession

    # Obtain a new token
    token = passtokens.new_token(db, user.id)

    # Generate the token url
    token_url = request.route_url('setpass', token = token)

    #Send the token to the user
    email.send(
        recipients = (user.fullname, user.email),
        subject = get_setting(db, "subject_forgot_token").str_value,
        template = get_setting(db, "template_forgot_token").str_value,
        values={
           'fullname' : user.fullname,
           'token_url' : token_url
           }
        )
    return token

@view_config(route_name='forgot_api', renderer='json')
def v_forgot_api(request):
    db = request.dbsession
    # Extract email from body
    try:
        req_email = request.json_body['email']
    except KeyError:
        return { 'success' : False, 'error' : 'INVALID_REQUEST' }

    if not re.match(r"[^@]+@[^@]+\.[^@]+", req_email):
        return { 'success' : False, 'error' : 'MALFORMED_EMAIL' }

    # Try to find user
    user = db.query(User).filter(User.email==req_email).one_or_none()

    if user is None:
        # Not returning an error on this one intentionally
        return { 'success' : True }

    # Generate a new forgot token and send it to the user
    token = send_forgot_token(request, user)

    log.debug(f"USER REQUESTED RECOVERY TOKEN: {token}")

    return { 'success' : True }

@view_config(route_name='forgot', renderer='../templates/forgot.pt')
def v_forgot(request):
    # Invalidate this session
    request.session.invalidate()

    return {
            'pagetitle' : 'DataMeta - Recover Password',
            }
