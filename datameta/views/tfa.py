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

from datetime import datetime
import json

from pyramid.httpexceptions import HTTPFound, HTTPNoContent, HTTPNotFound, HTTPForbidden
from pyramid.view import view_config

from sqlalchemy import and_

from .. import errors
from ..security import register_failed_login_attempt, tfaz, clear_failed_login_attempts
from ..models import User

import logging
log = logging.getLogger(__name__)


@view_config(route_name='set_otp', renderer='json', request_method="POST")
def setup_tfa(request):
    body = json.loads(request.body.decode())

    if body['token'] != "0":
        # Validate token
        dbtoken = tfaz.check_2fa_token(request.dbsession, body['token'])

        if dbtoken is None:
            return HTTPNotFound()

        if dbtoken and dbtoken.expires < datetime.now():
            # return HTTPGone()
            raise errors.get_validation_error(['The 2fa setup session has expired. Please reset your password.'])

        in_otp = body['inputOTP']
        error = tfaz.verify_otp(dbtoken.secret, in_otp)

        if error:
            raise errors.get_validation_error([error])

        dbtoken.user.tfa_secret = dbtoken.secret

        request.dbsession.delete(dbtoken)

    return HTTPNoContent()


@view_config(route_name='tfa', renderer='../templates/tfa.pt')
def tfa_view(request):
    if request.POST:
        try:
            # Obtain submitted data
            in_otp = request.POST['input_otp']

            user = request.dbsession.query(User).filter(and_(
                User.id == request.session['preauth_uid'],
                User.enabled.is_(True)
            )).one_or_none()

            if user is None:
                raise HTTPForbidden()

            if user.tfa_secret is None and tfaz.is_2fa_enabled():
                raise errors.get_validation_error(['Please reset your password and set up two-factor authorisation.'])

            error = tfaz.verify_otp(user.tfa_secret, in_otp)
            if error:
                register_failed_login_attempt(request.dbsession, user)
                if not user.enabled:
                    return HTTPFound(location="/login")

            else:

                if datetime.utcnow() < request.session["auth_expires"]:
                    request.session["user_uid"] = request.session["preauth_uid"]
                    request.session["user_gid"] = request.session["preauth_gid"]
                    del request.session["preauth_uid"]
                    del request.session["preauth_gid"]

                    clear_failed_login_attempts(user=user, dbsession=request.dbsession)
                    return HTTPFound(location="/home")
                else:
                    return HTTPFound(location="/login")

        except KeyError:
            pass
        return HTTPFound(location="/tfa")
    return {
            'page_title_current_page' : 'Login'
            }
