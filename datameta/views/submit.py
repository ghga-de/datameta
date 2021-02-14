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

@view_config(route_name='submit', renderer='../templates/submit.pt')
def v_submit(request):
    security.require_login(request)
    request.session['counter'] = request.session['counter'] + 1 if 'counter' in request.session else 0
    return {
            'counter' : request.session['counter']
            }

@view_config(route_name='submit_samplesheet', renderer="json")
def v_submit_samplesheet(request):
    # Re-validate user
    user = security.revalidate_user(request)

    success = []
    errors = {
            'missing_keys' : [],
            'duplicate_rows' : []
            }

    if request.POST:
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
    return {}

@view_config(route_name='submit_data', renderer="json")
def v_submit_data(request):
    # Re-validate user
    user = security.revalidate_user(request)

    if request.POST:
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
    return {}

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
                { m_rec.metadatum.name : formatted_mrec_value(m_rec) for m_rec in m_set.metadatumrecords }
                for m_set in m_sets]
            }

@view_config(route_name='v_submit_view_json', renderer="json")
def v_submit_view_json(request):
    # Re-validate user
    user = security.revalidate_user(request)

    # Obtain annotations and unannotated file information
    annotated    = get_pending_annotated(request.dbsession, user)
    unannotated  = get_pending_unannotated(request.dbsession, user)

    # Obtain annotated file names
    annotated_filenames = [ row[key] for row in annotated['table_data'] for key in annotated['mdat_names_files'] ]

    # Remove those from the unannotated data
    unannotated['table_data'] = [ elem for elem in unannotated['table_data'] if elem['filename'] not in annotated_filenames ]

    return {
            'annotated' : annotated,
            'unannotated' : unannotated
            }
