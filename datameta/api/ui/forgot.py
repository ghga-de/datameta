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

from pyramid.view import view_config

from ... import security, email
from ...settings import get_setting

import re
import logging
log = logging.getLogger(__name__)


def send_forgot_token(request, db_token_obj, clear_token):
    """Sends a password reset token email to the corresponding user"""
    db = request.dbsession

    token_url = request.route_url('setpass', token = clear_token)
    email.send(
        recipients = (db_token_obj.user.fullname, db_token_obj.user.email),
        subject = get_setting(db, "subject_forgot_token"),
        template = get_setting(db, "template_forgot_token"),
        values={
            'fullname' : db_token_obj.user.fullname,
            'token_url' : token_url
            }
        )

    log.debug("User requested recovery token.", extra={"clear_token": clear_token})


@view_config(route_name='forgot_api', renderer='json')
def v_forgot_api(request):
    db = request.dbsession
    # Extract email from body
    try:
        req_email = request.json_body['email']
        req_email = req_email.lower()  # Convert separately to maintain KeyError
    except KeyError:
        return { 'success' : False, 'error' : 'INVALID_REQUEST' }

    if not re.match(r"[^@]+@[^@]+\.[^@]+", req_email):
        return { 'success' : False, 'error' : 'MALFORMED_EMAIL' }

    try:
        db_token_obj, clear_token = security.get_new_password_reset_token_from_email(db, req_email)
    except KeyError:
        # User not found
        log.debug("Recovery token request. User could not be resolved.", extra={"req_email": req_email})
    else:
        # Generate a new forgot token and send it to the user
        send_forgot_token(request, db_token_obj, clear_token)
        log.debug("User requested recovery token.", extra={"clear_token": clear_token})

    return { 'success' : True }
