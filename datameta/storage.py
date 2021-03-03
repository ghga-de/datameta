# Copyright (c) 2021 Leon Kuchenbecker <leon.kuchenbecker@uni-tuebingen.de>
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

import os
import shutil
import logging
log = logging.getLogger(__name__)

def demo_mode(request):
    """Determine whether the application has been configured to be in demo mode"""
    return request.registry.settings.get('datameta.demo_mode') in [True, 'true', 'True']

def rm(request, storage_path):
    """Remove a file from storage by local storage file name"""
    if not demo_mode(request):
        os.remove(os.path.join(request.registry.settings['datameta.storage_path'], storage_path))
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

def write_file(request, db_file, file):
    # Find the output folder and try to create it if it does not exist
    outdir = request.registry.settings['datameta.storage_path']
    if not os.path.exists(outdir):
        os.mkdir(outdir)

    # Sanity checks and output path generation
    if db_file.storage_uri is None or not db_file.storage_uri.startswith("file://"):
        raise RuntimeError(f"Unable to store to storage URI '{db_file.storage_uri}'")
    out_path = os.path.join(outdir, db_file.storage_uri[7:]) # Strip the file:// prefix

    # Write the file
    if not demo_mode(request):
        file.seek(0)
        with open(out_path, 'wb') as outfile:
            shutil.copyfileobj(file, outfile)
        log.info(f"[STORAGE][NEWFILE][user={db_file.user.uuid}][file={db_file.uuid}]")
    else:
        log.info(f"[!!DEMOMODE!!][STORAGE][NEWFILE][user={db_file.user.uuid}][file={db_file.uuid}]")
