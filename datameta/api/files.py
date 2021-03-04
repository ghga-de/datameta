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

import logging
from dataclasses import dataclass
from pyramid.view import view_config
from pyramid.request import Request
from pyramid.httpexceptions import HTTPOk, HTTPNotFound, HTTPForbidden, HTTPConflict, HTTPBadRequest
from typing import Optional, Dict
from datetime import datetime, timedelta
from .. import models, siteid, security, storage, resource, errors
from . import DataHolderBase

log = logging.getLogger(__name__)

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
class FileResponse(FileBase):
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
    return FileUploadResponse(
            name              = db_file.name,
            file_id           = db_file.site_id,
            user_id           = db_file.user.site_id,
            group_id          = db_file.group.site_id,
            expires_at        = db_file.upload_expires.isoformat(),
            url_to_upload     = upload_url,
            request_headers   = request_headers,
            )

@view_config(
    route_name="files_id",
    renderer="json",
    request_method="GET",
    openapi=True
)
def get_file(request: Request) -> FileResponse:
    """Get details for a file.

    Raises:
        400 HTTPBadRequest - The request is malformed
        401 HTTPUnauthorized - Unauthorized access
        403 HTTPForbidden  - Requesting entity is not authorized to access this file
        404 HTTPNotFound   - The requested file ID cannot be found
    """
    # Check authentication and raise 401 if unavailable
    auth_user = security.revalidate_user(request)

    db = request.dbsession

    # Obtain file from database
    db_file = resource.resource_by_id(db, models.File, request.matchdict['id'])

    # Check if file could be found
    if db_file is None:
        raise HTTPNotFound(json=None)

    # Check if requesting user has access to the file. Group based!
    if db_file.group_id != auth_user.group_id:
        raise HTTPForbidden(json=None)

    # Return details
    return FileResponse(
            name              = db_file.name,
            file_id           = db_file.site_id,
            content_uploaded  = db_file.content_uploaded,
            checksum          = db_file.checksum,
            filesize          = db_file.filesize,
            user_id           = db_file.user.site_id,
            group_id          = db_file.group.site_id,
            expires_at        = db_file.upload_expires.isoformat() if db_file.upload_expires else None
            )

@view_config(
    route_name="files_id",
    renderer="json",
    request_method="PUT",
    openapi=True
)
def update_file(request: Request) -> HTTPOk:
    """Update not-submitted file."""
    db = request.dbsession

    # Check authentication and raise 401 if unavailable
    auth_user = security.revalidate_user(request)

    # Check if the requested resource exists and is still modifiable
    db_file = resource.resource_by_id(db, models.File, request.matchdict['id'])
    if db_file is None:
        raise HTTPNotFound(json=None) # 404
    if db_file.user_id != auth_user.id or db_file.group_id != auth_user.group_id:
        raise HTTPForbidden(json=None) # 403

    # We only allow any kind of modification until the file declared uploaded
    if db_file.content_uploaded:
        raise errors.get_validation_error(["Resource can no longer be modified."]) # 400

    # Update properties
    if 'checksum' in request.openapi_validated.body:
        db_file.checksum  = request.openapi_validated.body['checksum']
    if 'name' in request.openapi_validated.body:
        db_file.name      = request.openapi_validated.body['name']

    # Freeze the file
    if request.openapi_validated.body.get('contentUploaded'):
        try:
            storage.freeze(request, db_file)
        except storage.NoDataError:
            # No data has been uploaded yet
            raise errors.get_validation_error(["No data has been uploaded for this file."]) # 400
        except storage.NotWritableError:
            # File was frozen already
            raise errors.get_validation_error(["Resource can no longer be modified."]) # 400
        except storage.ChecksumMismatchError:
            # Checksum of uploaded data does not match announcement
            raise HTTPConflict(json=None) # 409
        log.info(f"[STORAGE][FREEZE][user={db_file.user.uuid}][file={db_file.uuid}]")

    return FileResponse(
            name              = db_file.name,
            file_id           = db_file.site_id,
            content_uploaded  = db_file.content_uploaded,
            checksum          = db_file.checksum,
            filesize          = db_file.filesize,
            user_id           = db_file.user.site_id,
            group_id          = db_file.group.site_id,
            expires_at        = db_file.upload_expires.isoformat() if db_file.upload_expires else None
            )

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
