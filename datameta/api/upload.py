# Copyright (c) 2021 Universität Tübingen, Germany
# Authors: Leon Kuchenbecker <leon.kuchenbecker@uni-tuebingen.de>
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

from pyramid.httpexceptions import HTTPNotFound, HTTPBadRequest, HTTPConflict, HTTPNoContent
from pyramid.view import view_config

import hashlib
import webob
from .. import resource, models, storage, security

@view_config(
    route_name="upload",
    renderer="json",
    request_method="POST",
)
def post(request) -> HTTPNoContent:
    """Handles POST requests against /api/upload to upload files.

    Raises:
        400 HTTPBadRequest - The request is malformed, i.e. the formdata field 'file' is not present or is not a file.
        404 HTTPNotFound   - The requested file ID cannot be found or is not handled by the datameta backend
        409 HTTPConflict   - Content was already uploaded for this file and the file was marked as completed by the submitting entity
        403 HTTPForbidden  - Requesting entity is not authorized to upload content for this file
    """
    db = request.dbsession

    # Validate authentication
    auth_user = security.revalidate_user(request)

    # Parse request header
    req_file     = request.POST.get("file")
    req_file_id  = request.matchdict.get("id")

    # Validate request header
    if req_file is None or req_file_id is None or not isinstance(req_file, webob.compat.cgi_FieldStorage):
        raise HTTPBadRequest(json=None)

    req_file_data = req_file.file

    # Try to find the references file in the database
    db_file = resource.resource_by_id(db, models.File, req_file_id)
    if db_file is None:
        raise HTTPNotFound(json=None)

    # Authorization
    if db_file.user_id != auth_user.id or db_file.group_id != auth_user.group_id:
        raise HTTPForbidden(json=None)

    # Verify that this file is still open for uploads
    if db_file.content_uploaded:
        raise HTTPConflict(json=None)

    # Verify that the file belongs in local storage
    if not db_file.storage_uri.startswith("file://"):
        raise HTTPNotFound(json=None)

    # Calculate the file size
    req_file_data.seek(0, 2)
    file_size = req_file_data.tell()
    req_file_data.seek(0)

    # Store the file on disk
    storage.write_file(request, db_file, req_file_data)

    return HTTPNoContent()
