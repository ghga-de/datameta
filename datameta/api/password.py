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

from pyramid.httpexceptions import HTTPNotFound, HTTPForbidden, HTTPGone

from pyramid.view import view_config

from .. import security, errors
from ..security import authz, tfaz
from ..models import User
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
    if request_id == '0':
        # Try to find the token
        token = security.get_password_reset_token(db, request_credential)
        if token is None:
            raise HTTPNotFound()  # 404 Token not found

        # Check if token expired
        if token is not None and token.expires < datetime.now():
            raise HTTPGone()  # 410 Token expired

        # Fetch the user corresponding to the token
        auth_user = token.user
    # Case B: Authenticated user changing their own password
    else:
        # Obtain authorized user
        auth_user = security.revalidate_user(request)  # raises 401 if unauthorizezd

        # Try to identify the target user by UUID
        target_user = resource_by_id(db, User, request_id)

        if target_user is None:
            raise HTTPForbidden()  # 403 User ID not found, hidden from the user intentionally

        # Only changing the user's own password is allowed
        if not authz.update_user_password(auth_user, target_user) or not security.check_password_by_hash(request_credential, auth_user.pwhash):
            raise HTTPForbidden()  # 403 Not authorized to change this user's password

    # Verify the password quality
    error = security.verify_password(db, auth_user.id, request_newPassword)
    if error:
        raise errors.get_validation_error([error])

    # Set the new password
    auth_user.pwhash = security.register_password(db, auth_user.id, request_newPassword)

    # Delete the password token if any
    if token:
        db.delete(token)

    tfa_token = ""
    if tfaz.is_2fa_enabled() and auth_user.tfa_secret is None:
        tfa_token, _ = tfaz.create_2fa_token(db, auth_user)

    return {
        "tfaToken": tfa_token
    }
