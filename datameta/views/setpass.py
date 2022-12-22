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

from .. import security
from ..api.ui.forgot import send_forgot_token

import datetime

import logging
log = logging.getLogger(__name__)


@view_config(route_name='setpass', renderer='../templates/setpass.pt')
def v_setpass(request):
    # Validate token
    dbtoken = security.get_password_reset_token(request.dbsession, request.matchdict['token'])

    unknown_token = dbtoken is None
    expired_token = not unknown_token and dbtoken.expires < datetime.datetime.now()

    # Token expired? Send new one.
    if expired_token:
        db_token_obj, clear_token = security.get_new_password_reset_token(request.dbsession, dbtoken.user)
        send_forgot_token(request, db_token_obj, clear_token)

    return {
        'page_title_current_page' : 'Set Password',
        'unknown_token' : unknown_token,
        'expired_token' : expired_token,
        'token_ok' : not unknown_token and not expired_token,
        'token' : request.matchdict['token'],
    }
