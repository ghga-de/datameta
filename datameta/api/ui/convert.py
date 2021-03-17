# Copyright (c) 2021 Universität Tübingen, Germany
# Authors: Leon Kuchenbecker <leon.kuchenbecker@uni-tuebingen.de>,
#          Kersten Breuer <k.breuer@dkfz.de>
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

from sqlalchemy.orm import joinedload

from pyramid.httpexceptions import HTTPBadRequest, HTTPOk
from pyramid.request import Request
from pyramid.view import view_config
import webob
import logging
import datetime

import pandas as pd

from ... import security, samplesheet, errors
from ...models import MetaDatum, MetaDataSet, MetaDatumRecord

log = logging.getLogger(__name__)

def formatted_mrec_value(value, datetimefmt):
    if datetimefmt is not None:
        try:
            return datetime.datetime.fromisoformat(value).strftime(datetimefmt)
        except ValueError:
            pass
    return value

####################################################################################################

def convert_samplesheet(db, file_like_obj, filename, user):
    # Try to read the sample sheet
    try:
        submitted_metadata = pd.read_excel(file_like_obj, dtype="object")
    except Exception as e:
        log.info(f"submitted sample sheet '{filename}' triggered exception {e}")
        raise samplesheet.SampleSheetReadError("Unable to parse the sample sheet.")

    # Query column names that we expect to see in the sample sheet (intra-submission duplicates)
    metadata              = db.query(MetaDatum).order_by(MetaDatum.order).all() 
    metadata_names        = [ datum.name for datum in metadata ]
    metadata_datetimefmt  = { datum.name : datum.datetimefmt for datum in metadata }

    missing_columns  = [ metadata_name for metadata_name in metadata_names if metadata_name not in submitted_metadata.columns ]
    if missing_columns:
        raise samplesheet.SampleSheetReadError(f"Missing columns: {', '.join(missing_columns)}.")

    # Limit the sample sheet to the columns of interest and drop duplicates
    submitted_metadata = submitted_metadata[metadata_names].drop_duplicates()

    # Convert all data to strings
    samplesheet.string_conversion(submitted_metadata, metadata)

    try:
        return [ { mdname : formatted_mrec_value(row[mdname], metadata_datetimefmt[mdname]) for mdname in metadata_names } for _, row in submitted_metadata.iterrows() ]
    except Exception as e:
        log.error(e)
        raise samplesheet.SampleSheetReadError("Unknown error")

####################################################################################################

@view_config(
    route_name      = "convert",
    renderer        = "json",
    request_method  = "POST",
)
def post(request: Request) -> HTTPOk:
    """Convert a spreadsheet to JSON metadatasets"""
    db = request.dbsession
    # Validate authorization or raise HTTPUnauthorized
    auth_user = security.revalidate_user(request)

    # Parse the request body
    if 'file' not in request.POST or not isinstance(request.POST['file'], webob.compat.cgi_FieldStorage):
        raise errors.get_validation_error(messages = [ "Invalid request" ])
    # Extract the submitted file from request body
    input_file = request.POST['file']
    input_file.file.seek(0)

    try:
        return convert_samplesheet(db, input_file.file, input_file.filename, auth_user)
    except samplesheet.SampleSheetReadError as e:
        log.warning(f"Sample sheet '{input_file.filename}' could not be read: {e}")
        raise errors.get_validation_error(messages = [ str(e) ])

