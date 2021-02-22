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

import bcrypt

from datameta.models import User

import logging
log = logging.getLogger(__name__)

def hash_password(pw):
    pwhash = bcrypt.hashpw(pw.encode('utf8'), bcrypt.gensalt())
    return pwhash.decode('utf8')

def check_password(pw, hashed_pw):
    expected_hash = hashed_pw.encode('utf8')
    return bcrypt.checkpw(pw.encode('utf8'), expected_hash)

@view_config(route_name='login', renderer='../templates/login.pt')
def my_view(request):
    request.session.invalidate()
    db = request.dbsession
    if request.POST:
        try:
            # Obtain submitted data
            in_email = request.POST['input_email']
            in_pwd   = request.POST['input_password']

            user = db.query(User).filter(User.email==in_email).one_or_none()
            if user and check_password(in_pwd, user.pwhash):
                request.session['user_uid'] = user.id
                request.session['user_gid'] = user.group.id
                request.session['user_email'] = user.email
                request.session['user_fullname'] = user.fullname
                request.session['user_groupname'] = user.group.name
                log.info(f"LOGIN [uid={user.id},email={user.email}] FROM [{request.client_addr}]")
                return HTTPFound(location="/home")
        except KeyError:
            pass
        return HTTPFound(location="/login")
    return {
            'pagetitle' : 'DataMeta - Login'
            }
