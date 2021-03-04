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

from dataclasses import dataclass
from pyramid.view import view_config
from pyramid.request import Request
from typing import Optional, List
from .. import models
from string import ascii_letters, digits
from random import choice
from .. import security
from pyramid.httpexceptions import HTTPOk, HTTPUnauthorized, HTTPForbidden
from ..resource import resource_by_id
from ..errors import get_validation_error
from datetime import datetime


@dataclass
class UserSession:
    """User Session as return object when requesting new ApiKey"""
    apikey_id: str
    user_id: str
    email: str
    token: str
    label: str
    expires_at: Optional[datetime]

    def __json__(self, request: Request) -> dict:
        return {
                "apiKeyId": self.apikey_id,
                "userId": self.user_id,
                "email": self.email,
                "token": self.token,
                "label": self.label,
                "expiresAt": self.expires_at.isoformat() if self.expires_at else None
            }


class ApiKeyLabels:
    """ApiKeyLabels container for OpenApi communication"""

    apikeys: List[dict]

    def __init__(self, user:models.User):
        self.apikeys = [
            {
                "apiKeyId": str(key.uuid),
                "label": key.label,
                "expiresAt": key.expires.isoformat() if key.expires else None,
            }
            for key in user.apikeys
        ]
    
    def __json__(self, request: Request) -> dict:
        return self.apikeys



def generate_api_key(request:Request, user:models.User, label:str):
    # For Token Composition:
    # Tokens consist of a core, which is stored as hash in the database,
    # plus a prefix that contains the user and the label of that ApiKey.
    # The user always provides the entire token, which is then split up
    # into prefic and core component. The prefix is used to identify the
    # ApiKey object in the database and the core component is matched
    # against the hash for validating it.
    token_core = "".join(choice(ascii_letters+digits) for _ in range(64) )
    token_prefix = f"{user.id}-{label}-"


    db = request.dbsession
    apikey = models.ApiKey(
        user_id = user.id,
        value = security.hash_password(token_core),
        label = label,
        expires = None
    )
    db.add(apikey)
    db.flush()

    return UserSession(
        apikey_id=str(apikey.uuid),
        user_id=user.site_id,
        email=user.email,
        token=apikey.value,
        label=apikey.label,
        expires_at=apikey.expires.isoformat() if apikey.expires else None
    )

@view_config(
    route_name="apikeys", 
    renderer='json', 
    request_method="POST", 
    openapi=True
)
def post(request:Request) -> UserSession:
    """Request new ApiKey"""
    try:
        auth_user = security.revalidate_user(request)
    except HTTPUnauthorized:
        if not {"email", "password"}.issubset(
            set(request.openapi_validated.body.keys())
        ):
            raise HTTPUnauthorized()

        email = request.openapi_validated.body["email"]
        password = request.openapi_validated.body["password"]

        auth_user = security.get_user_by_credentials(request, email, password)
        if not auth_user:
            raise HTTPUnauthorized()
        
    label = request.openapi_validated.body["label"]

    return generate_api_key(request, auth_user, label)


@view_config(
    route_name="user_id_keys", 
    renderer='json', 
    request_method="GET", 
    openapi=True
)
def get_user_keys(request:Request) -> UserSession:
    """Get all ApiKeys from a user"""
    
    auth_user = security.revalidate_user(request)
    
    db = request.dbsession
    target_user = resource_by_id(db, models.User, request.matchdict['id'])
    if not target_user or auth_user.id!=target_user.id:
        raise HTTPForbidden()
    
    return ApiKeyLabels(auth_user)

    
@view_config(
    route_name="apikeys_id", 
    renderer='json', 
    request_method="DELETE", 
    openapi=True
)
def delete_key(request:Request) -> UserSession:
    """Delete an ApiKey"""
    auth_user = security.revalidate_user(request)
    
    db = request.dbsession
    target_key = resource_by_id(db, models.ApiKey, request.matchdict['id'])
    if not target_key or auth_user.id!=target_key.user.id:
        raise HTTPForbidden()

    db.delete(target_key)

    return HTTPOk()
