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
from sqlalchemy import and_

from ..models import MetaDataSet
from .. import security

import uuid
import os
import shutil
import logging

import webob

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
    # Require login
    if not security.user_logged_in(request):
        return {}

    errors = {}

    if request.POST:
        print('POST data:', request.POST)
        for file_obj in request.POST.getall('files[]'):
            if  isinstance(file_obj, webob.compat.cgi_FieldStorage):
                input_file = file_obj.file
                out_path = os.path.join("/tmp", str(uuid.uuid4()))

                input_file.seek(0)
                try:
                    import_samplesheet(request, input_file, 0, 0)
                except SampleSheetColumnsIncompleteError as e:
                    log.debug(f"Sample sheet '{file_obj.filename}' failed because of missing columns {e.columns}")
                    errors[file_obj.filename] = e.columns

#                # DEBUG WRITE
#                with open(out_path, 'wb') as output_file:
#                    shutil.copyfileobj(input_file, output_file)
#                log.debug("SAMPLESHEET "+ out_path)
        return {
                'success' : True,
                'errors' : errors
                }
    return {}

@view_config(route_name='submit_data', renderer="json")
def v_submit_data(request):
    # Require login
    if not security.user_logged_in(request):
        return {}

    print("ENDPOINT")
    if request.POST:
        print('POST data:', request.POST)
        for file_obj in request.POST.getall('files[]'):
            if  isinstance(file_obj, webob.compat.cgi_FieldStorage):
                input_file = file_obj.file
                out_path = os.path.join("/tmp", str(uuid.uuid4()))

                input_file.seek(0)
                with open(out_path, 'wb') as output_file:
                    shutil.copyfileobj(input_file, output_file)
                print(out_path)
            else:
                log.warning("Ignoring files[] data in POST request - not of type FieldStorage")
        return {
                'success' : True
                }
    return {}

@view_config(route_name='pending_unannotated', renderer="json")
def v_pending_annotated(request):
    return {
            'table_data' : [
                ['EXMP_EASRU_R2.fastq.gz', '1.2 GB', '591785b794601e212b260e25925636fd'],
                ['EXMP_A8A1R_R1.fastq.gz', '831 MB', 'b1946ac92492d2347c6235b4d2611184'],

                ]
            }

@view_config(route_name='pending_annotated', renderer="json")
def v_pending_unannotated(request):
    user = security.revalidate_user(request)

    m_sets = request.dbsession.query(MetaDataSet).filter(and_(
        MetaDataSet.user==user,
        MetaDataSet.group==user.group,
        MetaDataSet.submission==None)
        ).all()
    return {
            'table_data' : [
                { m_rec.metadatum.name : m_rec.value for m_rec in m_set.metadatumrecords }
                for m_set in m_sets]
            }
