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

from pyramid.httpexceptions import HTTPNotFound, HTTPBadRequest, HTTPConflict, HTTPNoContent
from pyramid.view import view_config

import webob
import logging
from datetime import datetime
from .. import resource, models, storage, security

log = logging.getLogger(__name__)


@view_config(
    route_name="upload",
    renderer="json",
    request_method="POST",
)
def post(request) -> HTTPNoContent:
    """Handles POST requests against /api/upload to upload files.

    Raises:
        400 HTTPBadRequest - The request is malformed, i.e. the formdata field 'file' is not present or is not a file.
        404 HTTPNotFound   - The requested file ID cannot be found or is not handled by the datameta backend or access denied.
        409 HTTPConflict   - Content was already uploaded for this file and the file was marked as completed by the submitting entity
    """
    db = request.dbsession

    # Parse request header
    req_file     = request.POST.get("file")
    req_file_id  = request.matchdict.get("id")
    req_token    = request.headers.get("Access-Token")

    # Validate request header
    if req_file is None or req_file_id is None or not isinstance(req_file, webob.compat.cgi_FieldStorage):
        raise HTTPBadRequest(json=None)

    req_file_data = req_file.file

    # Try to find the references file in the database
    db_file = resource.resource_by_id(db, models.File, req_file_id)

    # Validate access token match
    db_file = db_file if db_file and req_token and db_file.upload_expires > datetime.now() and db_file.access_token == security.hash_token(req_token) else None

    if db_file is None:  # Includes token mismatch
        raise HTTPNotFound(json=None)

    # Verify that this file is still open for uploads
    if db_file.content_uploaded:
        raise HTTPConflict(json=None)

    # Verify that the file belongs in local storage
    if not db_file.storage_uri.startswith("file://"):
        raise HTTPNotFound(json=None)

    # Store the file on disk
    req_file_data.seek(0)
    storage.write_file(request, db_file, req_file_data)

    return HTTPNoContent()
