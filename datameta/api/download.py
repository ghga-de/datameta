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
from pyramid.httpexceptions import HTTPOk, HTTPTemporaryRedirect
from pyramid.request import Request
from datetime import datetime, timedelta
from .. import security, models, resource
from . import base_url, DataHolderBase
from .files import access_file_by_user


def generate_download_token(request:Request, file:models.File, expires_after:int):
    """
    Generate a Download Token and store unsalted hash in db.
    """
    token = security.generate_token()
    token_hash = security.hash_token(token)
    expires = datetime.now() + timedelta(minutes=float(expires_after))

    db = request.dbsession
    download_token = models.DownloadToken(
        file_id = file.id,
        value = token_hash,
        expires = expires
    )
    db.add(download_token)

    return token


@view_config(
    route_name = "rpc_get_file_url",
    renderer        = "json",
    request_method  = "GET",
    openapi         = True
)
def get_file_url(request) -> HTTPTemporaryRedirect:
    """Redirects to a temporary, pre-sign HTTP-URL for downloading a file.
    """
    file_id = request.openapi_validated.parameters.path['id']
    expires_after = request.openapi_validated.parameters.query['expires'] 
    auth_user = security.revalidate_user(request)

    # get file from db:
    db_file = access_file_by_user(
        request,
        user = auth_user,
        file_id = file_id
    )

    # create temporary download token:
    download_token = generate_download_token(
        request=request,
        file=db_file,
        expires_after=expires_after
    )

    return HTTPTemporaryRedirect(f"{base_url}/rpc/download/{download_token}")


@view_config(
    route_name = "rpc_download_token",
    renderer        = "json",
    request_method  = "GET",
    openapi         = True
)
def download_by_token(request) -> HTTPOk:
    """Download a file using a file download token.
    """
    token = request.matchdict['token']
    hashed_token = security.hash_token(token)

    db = request.dbsession
    db_token = db.query(models.DownloadToken).filter(
        models.DownloadToken.value==hashed_token
    ).one_or_none()

  
    # serve file:
    pass

    return HTTPOk()