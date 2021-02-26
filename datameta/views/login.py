# Copyright (c) 2021 Leon Kuchenbecker <leon.kuchenbecker@uni-tuebingen.de>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
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

import datameta

from datameta.models import User
from .. import security

import logging
log = logging.getLogger(__name__)

@view_config(route_name='login', renderer='../templates/login.pt')
def my_view(request):
    request.session.invalidate()
    db = request.dbsession
    if request.POST:
        try:
            # Obtain submitted data
            in_email = request.POST['input_email']
            in_pwd   = request.POST['input_password']

            auth_user = security.get_user_by_credentials(request, in_email, in_pwd)
            if auth_user:
                request.session['user_uid'] = auth_user.id
                request.session['user_gid'] = auth_user.group.id
                request.session['user_email'] = auth_user.email
                request.session['user_fullname'] = auth_user.fullname
                request.session['user_groupname'] = auth_user.group.name
                log.info(f"LOGIN [uid={auth_user.id},email={auth_user.email}] FROM [{request.client_addr}]")
                return HTTPFound(location="/home")
        except KeyError:
            pass
        return HTTPFound(location="/login")
    return {
            'pagetitle' : 'DataMeta - Login'
            }
