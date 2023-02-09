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

import logging
from dataclasses import dataclass
from pyramid.view import view_config
from pyramid.request import Request
from pyramid.httpexceptions import HTTPOk, HTTPNotFound, HTTPForbidden, HTTPConflict, HTTPNoContent
from typing import Optional
from datetime import datetime, timedelta
from .. import models, siteid, security, storage, resource, errors
from ..security import authz
from . import DataHolderBase

log = logging.getLogger(__name__)


class FileDeleteError(RuntimeError):
    pass


@dataclass
class FileBase(DataHolderBase):
    """Base class for File communication to OpenApi"""
    id          : dict
    name        : str
    user_id     : str
    expires  : Optional[str]


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


def delete_staged_file_from_db(file_id, db, auth_user):
    # Obtain file from database
    db_file = resource.resource_query_by_id(db, models.File, file_id).one_or_none()

    # Check if file could be found
    if db_file is None:
        raise HTTPNotFound(json=None)

    # Check if requesting user has access to the file
    if not authz.submit_file(auth_user, db_file):
        raise HTTPForbidden(json=None)

    if db_file.metadatumrecord is not None:
        raise errors.get_not_modifiable_error()

    user_uuid, file_uuid, storage_uri = db_file.user.uuid, db_file.uuid, db_file.storage_uri

    # Delete the database record
    db.delete(db_file)

    return user_uuid, file_uuid, storage_uri


def access_file_by_user(
    request: Request,
    user: models.User,
    file_id: str
) -> models.File:
    db = request.dbsession
    db_file = resource.resource_by_id(db, models.File, file_id)

    # Check if file could be found
    if db_file is None:
        raise HTTPNotFound(json_body=[])

    # Check if requesting user has access to the file
    if not authz.view_file(user, db_file):
        raise HTTPForbidden(json_body=[])

    return db_file


@view_config(
    route_name      = "rpc_delete_files",
    renderer        = "json",
    request_method  = "POST",
    openapi         = True
)
def delete_files(request: Request) -> HTTPNoContent:
    # Check authentication and raise 401 if unavailable
    auth_user = security.revalidate_user(request)

    db = request.dbsession

    deleted_files = [
        delete_staged_file_from_db(file_id, db, auth_user)
        for file_id in set(request.openapi_validated.body["fileIds"])
    ]

    # Commit transaction
    request.tm.commit()
    request.tm.begin()

    # Log the deletions from db
    for user_uuid, file_uuid, storage_uri in deleted_files:
        log.info("File record deleted from the database.", extra={"user_uuid": user_uuid, "file_uuid": file_uuid})
    # Delete the files from storage
    for user_uuid, file_uuid, storage_uri in deleted_files:
        storage.rm(request, storage_uri)
        log.info("File deleted from storage.", extra={"user_uuid": user_uuid, "file_uuid": file_uuid})

    return HTTPNoContent()


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

    if not req_name:
        raise errors.get_validation_error(["File names cannot be empty."])

    # Create the corresponding database object
    db_file = models.File(
            site_id           = siteid.generate(request, models.File),
            name              = req_name,
            checksum          = req_checksum,
            user_id           = auth_user.id,
            content_uploaded  = False,
            upload_expires    = datetime.now() + timedelta(days=1)  # TODO make this configurable
            )

    # INSERT the file and flush to obtain UUID for storage_uri generation
    db.add(db_file)
    db.flush()

    # Annotate internal storage path and obtain upload URL with request headers
    upload_url, request_headers = storage.create_and_annotate_storage(request, db_file)

    # Prepare response
    return FileUploadResponse(
            id                = resource.get_identifier(db_file),
            name              = db_file.name,
            user_id           = resource.get_identifier(db_file.user),
            expires        = db_file.upload_expires.isoformat(),
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

    test = request.matchdict['id']

    # Obtain file from database
    db_file = access_file_by_user(
        request,
        user = auth_user,
        file_id = test
    )

    # Return details
    return FileResponse(
            id                = resource.get_identifier(db_file),
            name              = db_file.name,
            content_uploaded  = db_file.content_uploaded,
            checksum          = db_file.checksum,
            filesize          = db_file.filesize,
            user_id           = resource.get_identifier(db_file.user),
            expires           = db_file.upload_expires.isoformat() if db_file.upload_expires else None
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
        raise HTTPNotFound(json=None)  # 404
    if not authz.submit_file(auth_user, db_file):
        raise HTTPForbidden(json=None)  # 403
    # We only allow modifications before the file is committed (uploaded)
    if db_file.content_uploaded:
        raise errors.get_not_modifiable_error()  # 403

    # Update properties
    if 'checksum' in request.openapi_validated.body:
        db_file.checksum  = request.openapi_validated.body['checksum']
    if 'name' in request.openapi_validated.body:
        updated_name      = request.openapi_validated.body['name']
        if not updated_name:
            raise errors.get_validation_error(["File names cannot be empty."])
        db_file.name = updated_name

    # Freeze the file
    if request.openapi_validated.body.get('contentUploaded'):
        try:
            storage.freeze(request, db_file)
        except storage.NoDataError:
            # No data has been uploaded yet
            raise errors.get_validation_error(["No data has been uploaded for this file."])  # 400
        except storage.NotWritableError:
            # File was frozen already
            raise errors.get_not_modifiable_error()  # 403
        except storage.ChecksumMismatchError:
            # Checksum of uploaded data does not match announcement
            raise HTTPConflict(json=None)  # 409
        log.info("Storage file frozen.", extra={"user_uuid": db_file.user.uuid, "file_uuid": db_file.uuid})

    return FileResponse(
            id                = resource.get_identifier(db_file),
            name              = db_file.name,
            content_uploaded  = db_file.content_uploaded,
            checksum          = db_file.checksum,
            filesize          = db_file.filesize,
            user_id           = resource.get_identifier(db_file.user),
            expires        = db_file.upload_expires.isoformat() if db_file.upload_expires else None
            )


def delete_files_db(db, db_files: list) -> list:
    """Deletes the specified db_files from the database and returns the
    storage_uris for subsequent deletion from storage after the transaction was
    committed.

    Raises:
        FileDeleteError - One of the specified files was already comitted and could thus not be deleted.
    """
    storage_uris = [ db_file.storage_uri for db_file in db_files ]
    for db_file in db_files:
        if db_file.metadatumrecord is not None:
            raise FileDeleteError(db_file.site_id)
        db.delete(db_file)

    return storage_uris


@view_config(
    route_name="files_id",
    renderer="json",
    request_method="DELETE",
    openapi=True
)
def delete_file(request: Request) -> HTTPNoContent:
    """Delete staged file.

    Raises:
        400 HTTPBadRequest   - The request is malformed
        401 HTTPUnauthorized - Unauthenticated access
        403 HTTPForbidden    - Requesting entity is not authorized to delete this file
        404 HTTPNotFound     - The requested file ID cannot be found
    """

    # Check authentication and raise 401 if unavailable
    auth_user = security.revalidate_user(request)

    db = request.dbsession

    user_uuid, file_uuid, storage_uri = delete_staged_file_from_db(request.matchdict['id'], db, auth_user)

    # Commit transaction
    request.tm.commit()
    request.tm.begin()
    log.info("File record deleted from the database.", extra={"user_uuid": user_uuid, "file_uuid": file_uuid})
    # Delete the file in storage if exists
    storage.rm(request, storage_uri)
    log.info("File deleted from storage.", extra={"user_uuid": user_uuid, "file_uuid": file_uuid})

    return HTTPNoContent()
