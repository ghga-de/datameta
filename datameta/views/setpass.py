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

from pyramid.httpexceptions import HTTPFound, HTTPNoContent, HTTPBadRequest, HTTPUnauthorized
from pyramid.view import view_config

from ..models import User, PasswordToken
from .. import security
from .forgot import send_forgot_token

import datetime

@view_config(route_name='setpass', renderer='../templates/setpass.pt')
def v_setpass(request):
    # Validate token
    dbtoken = security.get_password_reset_token(request.dbsession, request.matchdict['token'])

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
