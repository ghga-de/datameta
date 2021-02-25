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

from dataclasses import dataclass
from sqlalchemy.sql.elements import Null
from pyramid.view import view_config
from pyramid.request import Request
from typing import Optional, Dict
from ..models import ApiKey, User
from string import ascii_letters, digits
from random import choice
from .. import security
from pyramid.httpexceptions import HTTPUnauthorized
from datetime import datetime


@dataclass
class UserSession:
    """User Session as return object when requesting new ApiKey"""
    user_id: str
    email: str
    token: str
    expires_at: Optional[str]

    def __json__(self, request: Request) -> Dict[str, str]:
        return {
                "userId": self.user_id,
                "email": self.email,
                "token": self.token,
                "expiresAt": self.expires_at
            }

def generate_api_key(request:Request, user:User):
    token = "".join(choice(ascii_letters+digits) for _ in range(64) )

    db = request.dbsession
    apikey = ApiKey(
        user_id = user.id,
        value = token,
        comment = "",
        expires = None
    )
    db.add(apikey)

    return UserSession(
        user_id=str(apikey.user_id),
        email=user.email,
        token=apikey.value,
        expires_at=str(apikey.expires) if apikey.expires else None
    )

@view_config(
    route_name="apikeys", 
    renderer='json', 
    request_method="POST", 
    openapi=True
)
def post(request):
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

    return generate_api_key(request, auth_user)
    