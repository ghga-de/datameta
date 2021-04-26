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
from .. import security, models, storage
from . import base_url
from .files import access_file_by_user


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

    # retrieve URL:
    url = storage.get_download_url(
        request=request,
        db_file=db_file,
        expires_after=expires_after
    )

    return HTTPTemporaryRedirect(url)


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