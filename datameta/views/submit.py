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

from .. import models

import uuid
import os
import shutil
import logging

import webob

@view_config(route_name='submit', renderer='../templates/submit.pt')
def v_submit(request):
    if request.POST:
        input_file = request.POST['files[]'].file
        out_path = os.path.join("/tmp", str(uuid.uuid4()))

        input_file.seek(0)
        with open(out_path, 'wb') as output_file:
            shutil.copyfileobj(input_file, output_file)
        print(out_path)
    else:
        print(f"GET: {request.GET}")
    return {}

@view_config(route_name='submit_endpoint', renderer="json")
def v_submit_endpoint(request):
    print("ENDPOINT")
    if request.POST:
        print(request.POST)
        for file_obj in request.POST.getall('files[]'):
            if  isinstance(file_obj, webob.compat.cgi_FieldStorage):
                input_file = file_obj.file
                out_path = os.path.join("/tmp", str(uuid.uuid4()))

                input_file.seek(0)
                with open(out_path, 'wb') as output_file:
                    shutil.copyfileobj(input_file, output_file)
                print(out_path)
            else:
                logging.warning("Ignoring files[] data in POST request - not of type FieldStorage")
        return {
                'success' : True
                }
    else:
        return {}
    return {}
