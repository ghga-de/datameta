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

from .. import email
from ..settings import get_setting

def send_forgot_token(request, db_token_obj, clear_token):
    """Sends a password reset token email to the corresponding user"""
    db = request.dbsession

    email.send(
        recipients = (db_token_obj.user.fullname, db_token_obj.user.email),
        subject = get_setting(db, "subject_forgot_token").str_value,
        template = get_setting(db, "template_forgot_token").str_value,
        values={
           'fullname' : db_token_obj.user.fullname,
           'token_url' : request.route_url('setpass', token = clear_token)
           }
        )


@view_config(route_name='forgot', renderer='../templates/forgot.pt')
def v_forgot(request):
    # Invalidate this session
    request.session.invalidate()

    return {
            'pagetitle' : 'DataMeta - Recover Password',
            }
