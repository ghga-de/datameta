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
from pyramid.httpexceptions import HTTPNotFound, HTTPOk, HTTPTemporaryRedirect
from pyramid.request import Request
from pyramid.response import FileResponse
from datetime import datetime
from .. import security, models, storage
from ..resource import get_identifier
from .files import access_file_by_user
from sqlalchemy import and_


@view_config(
    route_name = "rpc_get_file_url",
    renderer        = "json",
    request_method  = "GET",
    openapi         = True
)
def get_file_url(request: Request) -> HTTPTemporaryRedirect:
    """Redirects to a temporary, pre-sign HTTP-URL for downloading a file.
    """
    file_id         = request.openapi_validated.parameters.path['id']
    expires_after   = request.openapi_validated.parameters.query['expires']
    auth_user       = security.revalidate_user(request)
    redirect        = request.openapi_validated.parameters.query['redirect']

    # get file from db:
    db_file = access_file_by_user(
        request,
        user = auth_user,
        file_id = file_id
    )

    # retrieve URL:
    url, expires_at = storage.get_download_url(
        request=request,
        db_file=db_file,
        expires_after=expires_after
    )

    response = {
            'fileId' : get_identifier(db_file),
            'fileUrl' : f"{request.host_url}{url}",
            'expires' : expires_at.isoformat() + "+00:00",
            'checksum' : db_file.checksum
            }

    if redirect:
        return HTTPTemporaryRedirect(url, json_body=response)
    else:
        return HTTPOk(json_body=response)


@view_config(
    route_name = "download_by_token",
    renderer        = "json",
    request_method  = "GET"
)
def download_by_token(request: Request) -> HTTPOk:
    """Download a file using a file download token.

    Usage: /download/{download_token}
    """
    token = request.matchdict['token']
    hashed_token = security.hash_token(token)

    # get download token from db
    db = request.dbsession
    db_token = db.query(models.DownloadToken).filter(
        and_(
            models.DownloadToken.value == hashed_token,
            models.DownloadToken.expires > datetime.utcnow()
        )
    ).one_or_none()

    if db_token is None:
        raise HTTPNotFound()

    # serve file:
    response = FileResponse(
        storage.get_local_storage_path(request, db_token.file.storage_uri),
        request=request,
        content_type='application/octet-stream'
    )
    response.content_disposition = f"attachment; filename=\"{db_token.file.name}\""

    return response
