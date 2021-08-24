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

from pyramid.httpexceptions import HTTPFound, HTTPNoContent, HTTPNotFound
from pyramid.view import view_config

from .. import security
from .. import resource
from ..models import User

from sqlalchemy import and_

from datetime import datetime

import json

import logging
log = logging.getLogger(__name__)

@view_config(route_name='setotp', renderer='json', request_method="POST")
def setup_twofa(request):
    body = json.loads(request.body.decode())

    user = request.dbsession.query(User).filter(and_(
        User.site_id == body["user"],
        User.enabled.is_(True)
    )).one_or_none()

    in_otp = body['inputOTP']
    otp_works = security.validate_2fa_token(user, in_otp)

    if not otp_works:
        return HTTPNotFound()

    return HTTPNoContent()

    if user:
        if security.validate_2fa_token(user, in_otp):
            ...
        

        

    




"""
@view_config(route_name='setpass', renderer='../templates/setpass.pt')
def v_setpass(request):
    # Validate token
    dbtoken = security.get_password_reset_token(request.dbsession, request.matchdict['token'])

    unknown_token = dbtoken is None
    expired_token = dbtoken is not None and dbtoken.expires < datetime.datetime.now()

    # Token expired? Send new one.
    if expired_token:
        db_token_obj, clear_token = security.get_new_password_reset_token(request.dbsession, dbtoken.user)
        send_forgot_token(request, db_token_obj, clear_token)

    twofa_setup_required = not unknown_token and not expired_token and dbtoken.user.tfa_secret is None
    twofa_uri = ""  # "MORGH!" if twofa_setup_required else ""

    if twofa_setup_required:
        secret = security.generate_2fa_secret()
        twofa_uri = security.generate_totp_uri(dbtoken.user, secret)
    

    return {
        'pagetitle' : 'DataMeta - Set Password',
        'unknown_token' : unknown_token,
        'expired_token' : expired_token,
        'token_ok' : not unknown_token and not expired_token,
        'token' : request.matchdict['token'],
        'twofa_setup_required' : twofa_setup_required,
        'twofa_uri' : twofa_uri,
    }
"""


@view_config(route_name='twofa', renderer='../templates/twofa.pt')
def my_view(request):
    if request.POST:
        try:
            # Obtain submitted data
            in_otp = request.POST['input_otp']
            
            user = request.dbsession.query(User).filter(and_(
                User.id == request.session['preauth_uid'],
                User.enabled.is_(True)
            )).one_or_none()

            if user and security.validate_2fa_token(user, in_otp):

                if datetime.utcnow() < request.session["auth_expires"]:
                    log.info(f"2FA [uid={user.id},email={user.email}] FROM [{request.client_addr}]")

                    request.session["user_uid"] = request.session["preauth_uid"]
                    request.session["user_gid"] = request.session["preauth_gid"]
                    del request.session["preauth_uid"]
                    del request.session["preauth_gid"]

                    return HTTPFound(location="/home")
                else:
                    return HTTPFound(location="/login")

        except KeyError:
            pass
        return HTTPFound(location="/twofa")
    return {
            'pagetitle' : 'DataMeta - Login'
            }
