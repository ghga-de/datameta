# Copyright 2021 Universität Tübingen
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

from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound

from sqlalchemy.exc import DBAPIError
from sqlalchemy import and_, or_

from ..models import MetaDataSet, File, MetaDatum, MetaDatumRecord, Submission
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

from ..samplesheet import import_samplesheet, SampleSheetReadError
from .. import storage, linting, siteid

class FileDeleteError(RuntimeError):
    pass

def submit_samplesheet(request, user):
    """Handle a samplesheet submission request"""
    success = []
    errors = []

    for file_obj in request.POST.getall('files[]'):
        if  isinstance(file_obj, webob.compat.cgi_FieldStorage):
            input_file = file_obj.file

            input_file.seek(0)
            try:
                n_added = import_samplesheet(request, input_file, user)
                success.append({
                    'filename' : file_obj.filename,
                    'n_added' : n_added
                    })
            except SampleSheetReadError as e:
                log.warning(f"Sample sheet '{file_obj.filename}' could not be read: {e}")
                errors.append({
                    'filename' : file_obj.filename,
                    'reason' : str(e)
                    })
    return {
            'success' : success,
            'errors' : errors
            }

def sizeof_fmt(num, suffix='B'):
    if num is None:
        return "unknown";
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
            return "%3.2f %s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.2f %s%s" % (num, 'Yi', suffix)


def formatted_mrec_value(mrec):
    if mrec.metadatum.datetimefmt is not None:
        try:
            return datetime.datetime.fromisoformat(mrec.value).strftime(mrec.metadatum.datetimefmt)
        except ValueError:
            pass
    return mrec.value


####################################################################################################
# VIEWS
####################################################################################################

@view_config(route_name='submit', renderer='../templates/submit.pt')
def v_submit(request):
    """Delivers the submission page"""
    security.revalidate_user_or_login(request)
    request.session['counter'] = request.session['counter'] + 1 if 'counter' in request.session else 0
    return {}
