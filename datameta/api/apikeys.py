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
from datetime import datetime, timedelta
from pyramid import threadlocal 


@dataclass
class UserSession:
    """User Session as return object when requesting new ApiKey"""
    apikey_id: str
    user_id: str
    email: str
    token: str
    label: str
    expires: Optional[datetime]

    def __json__(self, request: Request) -> dict:
        return {
                "apikeyId": self.apikey_id,
                "userId": self.user_id,
                "email": self.email,
                "token": self.token,
                "label": self.label,
                "expires": self.expires.isoformat() if self.expires else None
            }


class ApiKeyLabels:
    """ApiKeyLabels container for OpenApi communication"""

    apikeys: List[dict]

    def __init__(self, user:models.User):
        self.apikeys = [
            {
                "apikeyId": str(key.uuid),
                "label": key.label,
                "expires": key.expires.isoformat() if key.expires else None,
                "hasExpired": security.check_expiration(key.expires)
            }
            for key in user.apikeys
        ]
    
    def __json__(self, request: Request) -> dict:
        return self.apikeys


def get_expiration_date_from_str(expires_str:Optional[str]):
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
                messages=["Wrong datetime format. Please use isoformat."],
                fields=["expires"]
            )

        # check if chosen expiratio date exceeds max_expiration_datetime:
        if expires_datetime > max_expiration_datetime:
            raise get_validation_error(
                messages=[
                    (
                        "The defined expiration date exceeded"
                        " the max allowed expiration period, "
                        f"which is {max_expiration_period} days."
                    )
                ],
                fields=["expires"]
            )
    
    return expires_datetime
    

def generate_api_key(request:Request, user:models.User, label:str, expires:Optional[datetime]=None):
    """For Token Composition:
    Tokens consist of a core, which is stored as hash in the database,
    plus a prefix that contains the user and the label of that ApiKey.
    The user always provides the entire token, which is then split up
    into prefic and core component. The prefix is used to identify the
    ApiKey object in the database and the core component is matched
    against the hash for validating it.
    """
    token = "".join(choice(ascii_letters+digits) for _ in range(64) )
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
        apikey_id=str(apikey.uuid),
        user_id=user.site_id,
        email=user.email,
        token=token,
        label=apikey.label,
        expires=apikey.expires
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
    expires = request.openapi_validated.body.get("expires")

    expires_datetime = get_expiration_date_from_str(expires)

    return generate_api_key(request, auth_user, label, expires_datetime)


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
