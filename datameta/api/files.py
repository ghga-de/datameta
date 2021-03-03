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
from pyramid.httpexceptions import HTTPOk
from typing import Optional, Dict
from datetime import datetime, timedelta
from .. import models, siteid, security, storage
from . import DataHolderBase

@dataclass
class FileBase(DataHolderBase):
    """Base class for File communication to OpenApi"""
    name        : str
    file_id     : str
    user_id     : str
    group_id    : str
    expires_at  : Optional[str]

@dataclass
class FileUploadResponse(FileBase):
    """FileUploadResponse container for OpenApi communication"""
    url_to_upload    : str
    request_headers  : dict

@dataclass
class FileResponse(FileUploadResponse):
    """FileResponse container for OpenApi communication"""
    checksum          : str
    content_uploaded  : bool
    filesize          : Optional[int] = None

@view_config(
    route_name      = "files",
    renderer        = "json",
    request_method  = "POST",
    openapi         = True
)
def post(request: Request) -> FileUploadResponse:
    """Announce a file and get a URL for uploading it."""
    db = request.dbsession

    # Check authentication and raise 401 if unavailable
    auth_user = security.revalidate_user(request)

    # Extract request body fields
    req_name = request.openapi_validated.body["name"]
    req_checksum = request.openapi_validated.body["checksum"]

    # Create the corresponding database object
    db_file = models.File(
            site_id           = siteid.generate(request, models.File),
            name              = req_name,
            checksum          = req_checksum,
            user_id           = auth_user.id,
            group_id          = auth_user.group_id,
            content_uploaded  = False,
            upload_expires    = datetime.now() + timedelta(days=1) # TODO make this configurable
            )

    # INSERT the file and flush to obtain UUID for storage_uri generation
    db.add(db_file)
    db.flush()

    # Annotate internal storage path and obtain upload URL with request headers
    upload_url, request_headers = storage.annotate_storage(request, db_file)

    # Prepare response
    f = FileUploadResponse(
            name              = db_file.name,
            file_id           = db_file.site_id,
            user_id           = db_file.user.site_id,
            group_id          = db_file.group.site_id,
            expires_at        = db_file.upload_expires.isoformat(),
            url_to_upload     = upload_url,
            request_headers   = request_headers,
            )
    return f

@view_config(
    route_name="files_id",
    renderer="json",
    request_method="GET",
    openapi=True
)
def get_file(request: Request) -> FileResponse:
    """Get details for a file."""
    pass
    return {}

@view_config(
    route_name="files_id",
    renderer="json",
    request_method="PUT",
    openapi=True
)
def update_file(request: Request) -> HTTPOk:
    """Update not-submitted file."""
    pass
    return {}

@view_config(
    route_name="files_id",
    renderer="json",
    request_method="DELETE",
    openapi=True
)
def delete_file(request: Request) -> HTTPOk:
    """Delete not-submitted file."""
    pass
    return {}
