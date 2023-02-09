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

from ..security import tfaz
import datetime


@view_config(route_name='settfa', renderer='../templates/settfa.pt')
def v_settfa(request):

    tfa_qrcode = ""
    unknown_token, expired_token = False, False
    if request.matchdict['token'] != "0":
        # Validate token
        dbtoken = tfaz.check_2fa_token(request.dbsession, request.matchdict['token'])

        unknown_token = dbtoken is None
        expired_token = not unknown_token and dbtoken.expires < datetime.datetime.now()

        if not expired_token and not unknown_token:
            tfa_qrcode = tfaz.generate_2fa_qrcode(dbtoken.user, dbtoken.secret)

    return {
        'page_title_current_page' : 'Set 2FA',
        'unknown_token' : unknown_token,
        'expired_token': expired_token,
        'token_ok' : not unknown_token and not expired_token,
        'token' : request.matchdict['token'],
        'tfa_qrcode' : tfa_qrcode,
        'tfa_setup_required' : request.matchdict['token'] != "0",
    }
