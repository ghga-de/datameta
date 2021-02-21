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
from .login import hash_password
from .. import passtokens

import logging
log = logging.getLogger(__name__)

import re

@view_config(route_name='forgot_api', renderer='json')
def v_forgot_api(request):
    # Extract email from body
    try:
        email = request.json_body['email']
    except KeyError:
        return { 'success' : False, 'error' : 'INVALID_REQUEST' }

    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return { 'success' : False, 'error' : 'MALFORMED_EMAIL' }

    # Try to find user
    user = request.dbsession.query(User).filter(User.email==email).one_or_none()
    if user is None:
        # Not returning an error on this one intentionally
        return { 'success' : True }

    # Obtain a new token
    token = passtokens.new_token(request, user.id)

    # Send the token to the user
    # TODO
    log.debug(f"USER REQUESTED RECOVERY LINK: http://localhost:6543/setpass/{token}")

    return { 'success' : True }

@view_config(route_name='forgot', renderer='../templates/forgot.pt')
def v_forgot(request):
    # Invalidate this session
    request.session.invalidate()

    return {
            'pagetitle' : 'DataMeta - Recover Password',
            }
