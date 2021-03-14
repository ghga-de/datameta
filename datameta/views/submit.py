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
