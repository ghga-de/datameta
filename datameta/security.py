# Copyright (c) 2021 Universität Tübingen, Germany
# Authors: Leon Kuchenbecker <leon.kuchenbecker@uni-tuebingen.de>,
#          Kersten Breuer <k.breuer@dkfz.de>
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

from pyramid.httpexceptions import HTTPFound, HTTPUnauthorized

from .models import User, ApiKey

import bcrypt
import logging
log = logging.getLogger(__name__)

def verify_password(s):
    if len(s)<10:
        return "The password has to have a length of at least 10 characters."
    return None

def hash_password(pw):
    """Hash a password/token and return the salted hash"""
    pwhash = bcrypt.hashpw(pw.encode('utf8'), bcrypt.gensalt())
    return pwhash.decode('utf8')

def check_password_by_hash(pw, hashed_pw):
    """Check a password/hash against a salted hash"""
    expected_hash = hashed_pw.encode('utf8')
    return bcrypt.checkpw(pw.encode('utf8'), expected_hash)

def get_user_by_credentials(request, email:str, password:str):
    """Check a compination of email and password, returns a user object if valid"""
    db = request.dbsession
    user = db.query(User).filter(User.email==email).one_or_none()
    if user and check_password_by_hash(password, user.pwhash):
        return user
    return None

def get_bearer_token(request):
    """Extracts a Bearer authentication token from the request and returns it if present, None
    otherwise."""
    auth = request.headers.get("Authorization")
    if auth is not None:
        try:
            method, content = auth.split(" ")
            if method=="Bearer":
                return content
        except:
            pass
    return None

def revalidate_user(request):
    """Revalidate the currently logged in user and return the corresponding user object. On failure,
    raise a 401"""
    db = request.dbsession
    # Check for token based auth
    token = get_bearer_token(request)
    if token is not None:
        user = db.query(User).select_from(User).join(ApiKey).filter(ApiKey.value==token).one_or_none()
        if user is not None:
            log.info("APIKEY AUTH FROM '{user.email}'")
            return user

    # Check for session based auth
    if 'user_uid' not in request.session:
        request.session.invalidate()
        raise HTTPUnauthorized()
    user = request.dbsession.query(User).filter(User.id==request.session['user_uid']).one_or_none()
    # Check if the user still exists and their group hasn't changed
    if user is None or user.group_id != request.session['user_gid']:
        request.session.invalidate()
        raise HTTPUnauthorized()
    request.session['site_admin'] = user.site_admin
    request.session['group_admin'] = user.group_admin
    return user

def revalidate_user_or_login(request):
    """Revalidate and return the currently logged in user, on failure redirect to the login page"""
    try:
        return revalidate_user(request)
    except HTTPUnauthorized:
        raise HTTPFound("/login")

def revalidate_admin(request):
    """Revalidate the currently logged in user and return the corresponding user object. On failure
    or if the user is not a site or group admin, raise a 403"""
    user = revalidate_user(request)
    if user.site_admin or user.group_admin:
        return user
    raise HTTPUnauthorized()
