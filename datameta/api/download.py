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
from .. import security
from . import base_url

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
    expires = request.openapi_validated.parameters.query['expires'] 

    auth_user = security.revalidate_user(request)

    # check if file exists and get file object:
    pass

    # check if user is allowed to access file:
    pass

    # create temporary download token:
    pass
    download_token = "test_token"

    raise HTTPTemporaryRedirect(f"{base_url}/rpc/download/{download_token}", )


@view_config(
    route_name = "rpc_download_token",
    renderer        = "json",
    request_method  = "GET",
    openapi         = True
)
def download_by_token(request) -> HTTPOk:
    """Download a file using a file download token.
    """
    download_token = request.matchdict['token']
  
    # serve file:
    pass
    
    return HTTPOk()