# Copyright (c) 2021 Universität Tübingen, Germany
# Authors: Leon Kuchenbecker <leon.kuchenbecker@uni-tuebingen.de>
# # Permission is hereby granted, free of charge, to any person obtaining a copy
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
