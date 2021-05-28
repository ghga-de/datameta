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

from dataclasses import dataclass
from pyramid.view import view_config
from pyramid.request import Request
from typing import Optional, List
from .. import models
from .. import security
from ..security import authz
from pyramid.httpexceptions import HTTPOk, HTTPUnauthorized, HTTPForbidden
from ..resource import resource_by_id, get_identifier
from ..errors import get_validation_error
from datetime import datetime, timedelta
from pyramid import threadlocal
from . import DataHolderBase


@dataclass
class UserSession(DataHolderBase):
    """User Session as return object when requesting new ApiKey"""
    id: dict
    user_id: str
    token: str
    label: str
    expires: Optional[str]


class ApiKeyLabels:
    """ApiKeyLabels container for OpenApi communication"""

    apikeys: List[dict]

    def __init__(self, user: models.User):
        self.apikeys = [
            {
                "id": get_identifier(key),
                "label": key.label,
                "expires": key.expires.isoformat() if key.expires else None,
                "hasExpired": security.check_expiration(key.expires)
            }
            for key in user.apikeys
        ]

    def __json__(self, request: Request) -> List[dict]:
        return self.apikeys


def get_expiration_date_from_str(expires_str: Optional[str]):
    """Validates a user-defined ApiKey expiration date and converts it into a datetime object"""
    # calculated the latest expiration date allowed
    max_expiration_period = int(threadlocal.get_current_registry().settings['datameta.apikeys.max_expiration_period'])
    max_expiration_datetime = datetime.now() + timedelta(days=max_expiration_period)

    if expires_str is None:
        expires_datetime = max_expiration_datetime
    else:
        # check if str matches isoformat
        try:
            expires_datetime = datetime.fromisoformat(expires_str)
        except (ValueError, TypeError):
            raise get_validation_error(
                messages = ["Wrong datetime format. Please use isoformat."],
                fields = ["expires"]
            )

        # check if chosen expiratio date exceeds max_expiration_datetime:
        if expires_datetime > max_expiration_datetime:
            raise get_validation_error(
                messages = [
                    (
                        "The defined expiration date exceeded"
                        " the max allowed expiration period, "
                        f"which is {max_expiration_period} days."
                    )
                ],
                fields = ["expires"]
            )

    return expires_datetime


def generate_api_key(request: Request, user: models.User, label: str, expires: Optional[datetime] = None):
    """
    Generate API Token and store unsalted hash in db.
    """
    token = security.generate_token()
    token_hash = security.hash_token(token)

    db = request.dbsession
    apikey = models.ApiKey(
        user_id = user.id,
        value = token_hash,
        label = label,
        expires = expires
    )
    db.add(apikey)
    db.flush()

    return UserSession(
        id = get_identifier(apikey),
        user_id = get_identifier(user),
        token = token,
        label = apikey.label,
        expires = expires.isoformat() if expires else None
    )


@view_config(
    route_name = "apikeys",
    renderer = 'json',
    request_method = "POST",
    openapi = True
)
def post(request: Request) -> UserSession:
    """Request new ApiKey"""
    try:
        auth_user = security.revalidate_user(request)
    except HTTPUnauthorized:
        if not {"email", "password"}.issubset(
            set(request.openapi_validated.body.keys())
        ):
            raise HTTPUnauthorized()

        email = request.openapi_validated.body["email"].lower()
        password = request.openapi_validated.body["password"]

        auth_user = security.get_user_by_credentials(request, email, password)
        if not auth_user:
            raise HTTPUnauthorized()

    label = request.openapi_validated.body["label"]
    expires = request.openapi_validated.body.get("expires")

    expires_datetime = get_expiration_date_from_str(expires)

    return generate_api_key(request, auth_user, label, expires_datetime)


@view_config(
    route_name = "user_id_keys",
    renderer = 'json',
    request_method = "GET",
    openapi = True
)
def get_user_keys(request: Request) -> ApiKeyLabels:
    """Get all ApiKeys from a user"""

    auth_user = security.revalidate_user(request)

    db = request.dbsession
    target_user = resource_by_id(db, models.User, request.matchdict['id'])
    if not target_user or not authz.view_apikey(auth_user, target_user):
        raise HTTPForbidden()

    return ApiKeyLabels(auth_user)


@view_config(
    route_name = "apikeys_id",
    renderer = 'json',
    request_method = "DELETE",
    openapi = True
)
def delete_key(request: Request) -> UserSession:
    """Delete an ApiKey"""
    auth_user = security.revalidate_user(request)

    db = request.dbsession
    target_key = resource_by_id(db, models.ApiKey, request.matchdict['id'])
    if not target_key or not authz.delete_apikey(auth_user, target_key.user):
        raise HTTPForbidden()

    db.delete(target_key)

    return HTTPOk()
