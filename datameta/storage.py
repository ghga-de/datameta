# Copyright (c) 2021 Leon Kuchenbecker <leon.kuchenbecker@uni-tuebingen.de>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy # of this software and associated documentation files (the "Software"), to deal
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

import os
import shutil
import logging
import hashlib

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
        log.debug("DID NOT DELETE. DEMO MODE.")

def annotate_storage(request, db_file):
    """Returns an upload URL and corresponding request headers for uploading
    the referred file object and annotates the storage URI in the file
    object"""
    # Raise an error if this file object is not in the pre-upload stage
    if db_file.storage_uri is not None or db_file.content_uploaded:
        raise RuntimeError(f"File {db_file.uuid} cannot be annotated [storage_uri={db_file.storage_uri}; content_uploaded={db_file.content_uploaded}")

    # Currently, only local storage is supported
    db_file.storage_uri = f"file://{db_file.uuid}__{db_file.checksum}"
    return request.route_url('upload', id=db_file.uuid), {}

def get_local_storage_path(request, db_file):
    """Given a request and a database File object, determine the local storage path for the given db_file"""
    if db_file.storage_uri is None:
        raise NoDataError
    if not db_file.storage_uri.startswith("file://"):
        raise RuntimeError("Cannot obtain local storage path for non-local file object")
    # Find the output folder and try to create it if it does not exist
    outdir = request.registry.settings['datameta.storage_path']
    if not os.path.exists(outdir):
        os.mkdir(outdir)
    return os.path.join(outdir, db_file.storage_uri[7:]) # Strip the file:// prefix

def write_file(request, db_file, file):
    """Write the file content specified by 'file' to the storage denoted in 'db_file'"""
    # Sanity checks and output path generation
    if db_file.storage_uri is None or not db_file.storage_uri.startswith("file://"):
        raise RuntimeError(f"Unable to store to storage URI '{db_file.storage_uri}'")
    out_path = get_local_storage_path(request, db_file)

    # Write the file
    if not demo_mode(request):
        file.seek(0)
        with open(out_path, 'wb') as outfile:
            shutil.copyfileobj(file, outfile)
        log.info(f"[STORAGE][NEWFILE][user={db_file.user.uuid}][file={db_file.uuid}]")
    else:
        log.info(f"[!!DEMOMODE!!][STORAGE][NEWFILE][user={db_file.user.uuid}][file={db_file.uuid}]")

def _freeze_local(request, db_file):
    # Perform checksum comparison
    try:
        with open(get_local_storage_path(request, db_file), 'rb') as infile:
            # Calculate filesize
            infile.seek(0,2)
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
        raise NoDataError() # No data has been uploaded yet
    if db_file.content_uploaded:
        raise NotWritableError() # Data has been uploaded and file was frozen already
    if db_file.storage_uri.startswith("file://"):
        return _freeze_local(request, db_file)
    if db_file.storage_uri.startswith("s3://"):
        return _freeze_s3(request, db_file)
    raise NotImplementedError()
