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

from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound

from sqlalchemy.exc import DBAPIError
from sqlalchemy import and_, or_

from ..models import MetaDataSet, File, MetaDatum, MetaDatumRecord
from .. import security

import uuid
import os
import shutil
import logging
import hashlib

import webob
import datetime

import logging
log = logging.getLogger(__name__)

from ..samplesheet import import_samplesheet, SampleSheetColumnsIncompleteError
from .. import storage

def submit_samplesheet(request, user):
    """Handle a samplesheet submission request"""
    success = []
    errors = {
            'missing_keys' : [],
            'duplicate_rows' : []
            }

    for file_obj in request.POST.getall('files[]'):
        if  isinstance(file_obj, webob.compat.cgi_FieldStorage):
            input_file = file_obj.file
            out_path = os.path.join("/tmp", str(uuid.uuid4()))

            input_file.seek(0)
            try:
                n_added = import_samplesheet(request.dbsession, input_file, user)
                success.append({
                    'filename' : file_obj.filename,
                    'n_added' : n_added
                    })
            except SampleSheetColumnsIncompleteError as e:
                log.debug(f"Sample sheet '{file_obj.filename}' failed because of missing columns {e.columns}")
                errors['missing_keys'].append({
                    'filename' : file_obj.filename,
                    'keys' : e.columns
                    })
    return {
            'success' : success,
            'errors' : errors
            }

def submit_data(request, user):
    """Handle a data submission request"""
    log.debug("SUBMIT DATA")
    for file_obj in request.POST.getall('files[]'):
        if  isinstance(file_obj, webob.compat.cgi_FieldStorage):
            # Obtain the file object and filename
            http_file = file_obj.file
            http_filename = file_obj.filename
            http_file.seek(0)

            log.debug(f"User {user.id} is submitting file '{http_filename}'")

            # Calculate the MD5 hash
            md5 = hashlib.md5(http_file.read()).hexdigest()
            http_file.seek(0)

            # Calculate the file size
            http_file.seek(0, 2)
            file_size = http_file.tell()
            http_file.seek(0)

            # TODO replace this with action data storage
            outpath = "/tmp/datameta"
            if not os.path.exists(outpath):
                os.mkdir(outpath)


            savepoint = request.tm.savepoint()
            # Do we already have a pending file with the same name? Then we're overwriting.
            f_matches = request.dbsession\
                    .query(File)\
                    .select_from(File)\
                    .outerjoin(MetaDatumRecord)\
                    .outerjoin(MetaDataSet)\
                    .filter(
                            File.name == http_filename,         # Match filename
                            File.user_id == user.id,            # Match user
                            File.group_id == user.group_id,     # Match group
                            MetaDataSet.submission_id == None,  # submission either null because join failed (unannotated) or because it's not submitted (annotated)
                            ).all()

            # We shall only have one version of one file using the same filename pending for a
            # single uid/gid combination at the same time.
            if len(f_matches) > 1:
                log.error(f"File '{http_filename}' is pending multiple times for the same user {user.id} and group {user.group_id}")
                raise HTTPInternalServerError()

            old_name_storage = None
            if f_matches:
                # We have a file under this name pending already
                f = f_matches[0]
                f.checksum = md5
                f.filesize = file_size
                old_name_storage = f.name_storage
            else:
                # We're creating a new file
                f = File(name = http_filename,
                        checksum = md5,
                        filesize = file_size,
                        user_id = user.id,
                        group_id = user.group_id
                        )
                request.dbsession.add(f)
                request.dbsession.flush()

            name_storage = f"{str(f.id).rjust(10,'0')}_{user.id}_{user.group_id}_{file_size}_{md5}"
            out_path = os.path.join(outpath, name_storage);
            try:
                # Try to write the file to the desired location on the storage backend
                with open(out_path, 'wb') as output_file:
                    shutil.copyfileobj(http_file, output_file)
                # Update the database record to hold the local storage name
                f.name_storage = name_storage
                request.dbsession.add(f)
            except:
                # If an error occors, roll back the transaction and report the error
                savepoint.rollback()
                log.error("WRITE FAILED")
        else:
            log.warning("Ignoring files[] data in POST request - not of type FieldStorage")
    return {
            'success' : True
            }

def sizeof_fmt(num, suffix='B'):
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
            return "%3.2f %s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.2f %s%s" % (num, 'Yi', suffix)


def get_pending_unannotated(dbsession, user):
    # Find files that have not yet been associated with metadata
    files = dbsession.query(File).filter(and_(File.user_id==user.id, File.group_id==user.group_id, File.metadatumrecord==None)).order_by(File.id.desc())
    return {
            'table_data' : [
                {
                    'file_id' : file.id,
                    'filename' : file.name,
                    'filesize' : sizeof_fmt(file.filesize),
                    'checksum' : file.checksum
                    } for file in files
                ]
            }

def formatted_mrec_value(mrec):
    if mrec.metadatum.datetimefmt is not None:
        try:
            return datetime.datetime.fromisoformat(mrec.value).strftime(mrec.metadatum.datetimefmt)
        except ValueError:
            return "invalid"
    else:
        return mrec.value


def get_pending_annotated(dbsession, user):
    # Query metadata fields
    mdats = dbsession.query(MetaDatum).order_by(MetaDatum.order).all()
    mdat_names = [ mdat.name for mdat in mdats ]
    mdat_names_files = [ mdat.name for mdat in mdats if mdat.isfile ]

    # Query metadatasets that have been no associated submission
    m_sets = dbsession.query(MetaDataSet).filter(and_(
        MetaDataSet.user==user,
        MetaDataSet.group==user.group,
        MetaDataSet.submission==None)
        ).all()
    return {
            'mdat_names' : mdat_names,
            'mdat_names_files' : mdat_names_files,
            'table_data' : [
                {
                    'mset_id' : m_set.id,
                    'mset_values' : { m_rec.metadatum.name : formatted_mrec_value(m_rec) for m_rec in m_set.metadatumrecords }
                } for m_set in m_sets]
            }

def delete_mdatset(request, user):
    """Handles a metadataset deletion request. This function will only delete
    metadatasets which have not been submitted (committed) yet!!"""

    if 'mdatset_id' in request.POST:
        mdatset = request.dbsession\
                .query(MetaDataSet)\
                .filter(and_(MetaDataSet.id==int(request.POST['mdatset_id']), MetaDataSet.submission_id == None))\
                .one_or_none()
        if mdatset is not None:
            # Delete all metadata in this metadataset
            request.dbsession.query(MetaDatumRecord).filter(MetaDatumRecord.metadataset_id==mdatset.id).delete()
            # Delete the metadataset
            request.dbsession.delete(mdatset);

            request.dbsession.flush();
            return { 'success' : True }
    else:
        log.warning("Invalid metadataset deletion request received, no ID provided.")
    return { 'success' : False }

def delete_file(request, user):
    """Handles a metadataset deletion request. This function will only delete
    metadatasets which have not been submitted (committed) yet!!"""

    if 'file_id' in request.POST:
        file = request.dbsession\
                .query(File)\
                .filter(File.id==int(request.POST['file_id']))\
                .one_or_none()
        if file is not None:
            # Check if this file is not yet committed
            if file.metadatumrecord is not None:
                return { 'success' : False}

            # Remember the file path in storage
            storage_path = file.name_storage
            file_id      = file.id

            # Delete the file in the database
            request.dbsession.delete(file);
            request.dbsession.flush();

            # Delete the file in storage
            storage.rm(request, storage_path)

            log.info(f"DELETE PENDING FILE [uid={user.id},email={user.email},file_id={file_id}] FROM [{request.client_addr}]")

            return { 'success' : True }
    else:
        log.warning("Invalid file deletion request received, no ID provided.")
    return { 'success' : False }

####################################################################################################
# VIEWS
####################################################################################################

@view_config(route_name='submit', renderer='../templates/submit.pt')
def v_submit(request):
    """Delivers the submission page"""
    security.require_login(request)
    request.session['counter'] = request.session['counter'] + 1 if 'counter' in request.session else 0
    return {}

@view_config(route_name='submit_action', renderer="json")
def v_submit_action(request):
    """Responds to action requests made by the user on the submission page"""
    # Re-validate user
    user = security.revalidate_user(request)

    if request.POST:
        if 'action' in request.POST:
            action = request.POST['action']
            if action == "submit_data":
                return submit_data(request, user)
            elif action == "submit_samplesheet":
                return submit_samplesheet(request, user)
            elif action == "delete_mdatset":
                return delete_mdatset(request, user)
            elif action == "delete_file":
                return delete_file(request, user)
    log.warning("Invalid request received for /submit/action.")

@view_config(route_name='v_submit_view_json', renderer="json")
def v_submit_view_json(request):
    """Delivers data to be displayed on the submission page"""
    # Re-validate user
    user = security.revalidate_user(request)

    # Obtain annotations and unannotated file information
    annotated    = get_pending_annotated(request.dbsession, user)
    unannotated  = get_pending_unannotated(request.dbsession, user)

    # Obtain annotated file names
    annotated_filenames = [ row['mset_values'][key] for row in annotated['table_data'] for key in annotated['mdat_names_files'] ]

    # Remove those from the unannotated data
    unannotated['table_data'] = [ elem for elem in unannotated['table_data'] if elem['filename'] not in annotated_filenames ]

    return {
            'annotated' : annotated,
            'unannotated' : unannotated
            }
