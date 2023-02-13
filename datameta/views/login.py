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

from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config

from .. import security, errors
from ..security import tfaz, clear_failed_login_attempts

from datetime import datetime, timedelta
import logging
log = logging.getLogger(__name__)


@view_config(route_name='login', renderer='../templates/login.pt')
def my_view(request):
    request.session.invalidate()
    if request.POST:
        try:
            # Obtain submitted data
            in_email = request.POST['input_email']
            in_email = in_email.lower()  # Convert separately to maintain KeyError
            in_pwd   = request.POST['input_password']

            auth_user = security.get_user_by_credentials(request, in_email, in_pwd)
            if auth_user:
                log.info("User logged in.", extra={"user_id": auth_user.id, "email": auth_user.email, "client_addr": request.client_addr})

                tfa_enabled = tfaz.is_2fa_enabled()

                if tfa_enabled:
                    if auth_user.tfa_secret is None:
                        raise errors.get_validation_error(
                            ['Please reset your password and set up two-factor authorisation.'])
                    request.session["preauth_uid"] = auth_user.id
                    request.session["preauth_gid"] = auth_user.group_id
                    request.session["auth_expires"] = datetime.utcnow() + timedelta(minutes = 5)
                    return HTTPFound(location='/tfa')

                if not tfa_enabled:
                    request.session["user_uid"] = auth_user.id
                    request.session["user_gid"] = auth_user.group_id
                    request.session["auth_expires"] = datetime.utcnow() + timedelta(minutes = 5)
                    clear_failed_login_attempts(user=auth_user, dbsession=request.dbsession)
                    return HTTPFound(location='/home')

        except KeyError:
            pass
        return HTTPFound(location="/login")
    return {
            'page_title_current_page' : 'Login'
            }
