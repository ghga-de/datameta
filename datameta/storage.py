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

import os
import shutil
import logging
import hashlib
from datetime import datetime, timedelta
from pyramid.request import Request
from typing import Optional
from . import security, models
from .api import base_url

log = logging.getLogger(__name__)


class ChecksumMismatchError(RuntimeError):
    pass


class NotWritableError(RuntimeError):
    pass


class NoDataError(RuntimeError):
    pass


def demo_mode(request):
    """Determine whether the application has been configured to be in demo mode"""
    return request.registry.settings.get('datameta.demo_mode') in [True, 'true', 'True']


def rm(request, storage_path):
    """Remove a file from storage by local storage file name"""
    if not demo_mode(request):
        if storage_path.startswith("file://"):
            os.remove(os.path.join(request.registry.settings['datameta.storage_path'], storage_path[7:]))
        else:
            raise NotImplementedError()
    else:
        log.debug("Did not delete, demo mode.")


def get_local_storage_path(request, storage_uri):
    """Given a request and a database File object, determine the local storage path for the given storage_uri"""
    if storage_uri is None:
        raise NoDataError
    if not storage_uri.startswith("file://"):
        raise RuntimeError("Cannot obtain local storage path for non-local file object")
    # Find the output folder and try to create it if it does not exist
    outdir = request.registry.settings['datameta.storage_path']
    if not os.path.exists(outdir):
        os.mkdir(outdir)
    return os.path.join(outdir, storage_uri[7:])  # Strip the file:// prefix


def create_and_annotate_storage(request, db_file):
    """Returns an upload URL and corresponding request headers for uploading
    the referred file object and annotates the storage URI in the file
    object"""
    # Raise an error if this file object is not in the pre-upload stage
    if db_file.storage_uri is not None or db_file.content_uploaded:
        raise RuntimeError(f"File {db_file.uuid} cannot be annotated [storage_uri={db_file.storage_uri}; content_uploaded={db_file.content_uploaded}")

    # Currently, only local storage is supported
    db_file.storage_uri = f"file://{db_file.uuid}__{db_file.checksum}"

    token = security.generate_token()
    db_file.access_token = security.hash_token(token)

    # Create empty file
    open(get_local_storage_path(request, db_file.storage_uri), 'w').close()

    # Return the Upload URL
    return request.route_url('upload', id = db_file.uuid), { 'Access-Token' : token }


def write_file(request, db_file, file):
    """Write the file content specified by 'file' to the storage denoted in 'db_file'"""
    # Sanity checks and output path generation
    if db_file.storage_uri is None or not db_file.storage_uri.startswith("file://"):
        raise RuntimeError(f"Unable to store to storage URI '{db_file.storage_uri}'")
    out_path = get_local_storage_path(request, db_file.storage_uri)

    # Write the file
    if not demo_mode(request):
        file.seek(0)
        with open(out_path, 'wb') as outfile:
            shutil.copyfileobj(file, outfile)
        log.info("New file in storage.", extra={"user_uuid": db_file.user.uuid, "file_uuid": db_file.uuid})
    else:
        log.info("Demomode. New file in storage.", extra={"user_uuid": db_file.user.uuid, "file_uuid": db_file.uuid})


def _freeze_local(request, db_file):
    # Perform checksum comparison
    try:
        with open(get_local_storage_path(request, db_file.storage_uri), 'rb') as infile:
            # Calculate filesize
            infile.seek(0, 2)
            filesize = infile.tell()
            infile.seek(0)
            # Calculate checksum
            md5 = hashlib.md5(infile.read()).hexdigest()
        if md5 != db_file.checksum:
            raise ChecksumMismatchError()
        # Denote the filesize and mark the file as uploaded
        db_file.filesize          = filesize
        db_file.content_uploaded  = True
    except FileNotFoundError:
        raise NoDataError()


def _freeze_s3(request, db_file):
    # TODO
    # - Move object to another S3 object unaccessible by presigned URL
    # - Calculate MD5 for copied S3 object, if mismatch delete it and raise error
    # - Update the storage_uri to the new S3 object
    # - Delete old S3 object for which presigned URL was issued?
    # - Mark file as uploaded
    raise NotImplementedError()


def freeze(request, db_file):
    """Freezes a File. This function ensures that data is present, consistent
    with the pre-announced checksum and if that is the case, calculates and
    annotates the filesize and marks the file as content_uploaded

    Args:
        request - The calling HTTP request
        db_file - The database 'File' object

    Raises:
        NoDataError - No data was uploaded for this file yet
        NotWritableError - The file was already frozen
        ChecksumMismatchError - The uploaded data does not match the pre-announced checksum
    """
    if db_file.storage_uri is None:
        raise NoDataError()  # No data has been uploaded yet
    if db_file.content_uploaded:
        raise NotWritableError()  # Data has been uploaded and file was frozen already
    if db_file.storage_uri.startswith("file://"):
        return _freeze_local(request, db_file)
    if db_file.storage_uri.startswith("s3://"):
        return _freeze_s3(request, db_file)
    raise NotImplementedError()


def _get_download_url_local(request: Request, db_file: models.File, expires_after: Optional[int] = None):
    if expires_after is None:
        expires_after = 1

    token = security.generate_token()
    token_hash = security.hash_token(token)
    expires = datetime.utcnow() + timedelta(minutes = float(expires_after))

    db = request.dbsession
    download_token = models.DownloadToken(
        file_id = db_file.id,
        value = token_hash,
        expires = expires
    )
    db.add(download_token)

    return f"{base_url}/download/{token}", expires


def _get_download_url_s3(request: Request, db_file: models.File, expires_after: Optional[int] = None):
    # TODO
    raise NotImplementedError()


def get_download_url(request: Request, db_file: models.File, expires_after: Optional[int] = None):
    """Get a presigned URL to download a file

    Args:
        request (Request): The calling HTTP request
        db_file (models.File): The database 'File' object
        expires_after (Optional[int]): Number of minutes after which the URL will expire
    """
    if db_file.storage_uri is None:
        raise NoDataError()  # No data has been uploaded yet
    if db_file.storage_uri.startswith("file://"):
        return _get_download_url_local(request, db_file, expires_after = expires_after)
    if db_file.storage_uri.startswith("s3://"):
        return _get_download_url_s3(request, db_file, expires_after = expires_after)
    raise NotImplementedError()
