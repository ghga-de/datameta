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

from pyramid.httpexceptions import HTTPNoContent, HTTPNotFound, HTTPForbidden, HTTPBadRequest, HTTPGone

from pyramid.view import view_config

from .. import security, errors
from ..models import User, PasswordToken
from uuid import UUID
from datetime import datetime

from ..resource import resource_by_id

@view_config(
    route_name="SetUserPassword",
    renderer='json',
    request_method="PUT",
    openapi=True
)
def put(request):
    db = request.dbsession

    request_id = request.matchdict['id']
    request_newPassword = request.openapi_validated.body["newPassword"]
    request_credential = request.openapi_validated.body["passwordChangeCredential"]

    # Case A: Password reset token
    token = None
    if request_id=='0':
        # Try to find the token
        token = db.query(PasswordToken).filter(PasswordToken.value==request_credential).one_or_none()
        if token is None:
            raise HTTPNotFound() # 404 Token not found

        # Check if token expired
        if token is not None and token.expires < datetime.now():
            raise HTTPGone() # 410 Token expired

        # Fetch the user corresponding to the token
        auth_user = token.user
        target_user = auth_user
    # Case B: Authenticated user changing their own password
    else:
        # Obtain authorized user
        auth_user = security.revalidate_user(request) # raises 401 if unauthorizezd

        # Try to identify the target user by UUID
        target_user = resource_by_id(db, User, request_id)

        if target_user is None:
            raise HTTPForbidden() # 403 User ID not found, hidden from the user intentionally

        # Only changing the user's own password is allowed
        if auth_user.id != target_user.id or not security.check_password_by_hash(request_credential, auth_user.pwhash):
            raise HTTPForbidden() # 403 Not authorized to change this user's password

    # Verify the password quality
    error = security.verify_password(request_newPassword)
    if error:
        raise errors.get_validation_error([error])

    # Set the new password
    auth_user.pwhash = security.hash_password(request_newPassword)

    # Delete the password token if any
    if token:
        db.delete(token)

    return HTTPNoContent() # 204 all went well
