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
from pyramid.request import Request
from .. import models
from .. import security
from ..security import authz
from pyramid.httpexceptions import HTTPOk, HTTPForbidden, HTTPNotFound
from ..resource import resource_by_id


@view_config(
    route_name = "totp_secret_id",
    renderer = 'json',
    request_method = "DELETE",
    openapi = True
)
def delete_totp_secret(request: Request):
    """Delete a user's TOTP secret"""
    auth_user = security.revalidate_user(request)

    db = request.dbsession
    target_user = resource_by_id(db, models.User, request.matchdict['id'])
    if not target_user:
        raise HTTPNotFound()
    if not authz.delete_totp_secret(auth_user):
        raise HTTPForbidden()

    target_user.tfa_secret = None
    db.flush()

    return HTTPOk()
