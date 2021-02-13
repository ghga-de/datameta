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

from pyramid.httpexceptions import HTTPFound, HTTPUnauthorized

from .models import User

def revalidate_user(request):
    user = request.dbsession.query(User).filter(User.id==request.session['user_uid']).one_or_none()
    # Check if the user still exists
    if user is None:
        request.session.invalidate()
        raise HTTPUnauthorized()
    # Check if the group membership is still valid
    if user.group_id != request.session['user_gid']:
        # Ask the user to log back in
        raise HTTPFound("/login")
    return user

def user_logged_in(request):
    """Check if a user is logged in
    """
    return 'user_uid' in request.session

def require_login(request):
    """Check if a user is logged in and raise a redirect to the login page if not
    """
    if not user_logged_in(request):
        request.session.invalidate()
        raise HTTPFound("/login")

def admin_logged_in(request):
    """Check if a user is logged in
    """
    return 'user_gid' in request.session and request.session['user_gid']==0

def require_admin(request):
    """Check if an admin is logged in and raise a redirect to root if not
    """
    if not admin_logged_in(request):
        raise HTTPFound("/")
