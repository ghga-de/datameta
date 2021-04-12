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

def determine_separator(f, separators=",;\t:"):
    def get_line_seps(f, header=False):
        try:
            line = next(f).decode()
        except StopIteration:
            raise ValueError("Empty file." if header else "No data in file.")
        return sorted(((line.count(sep), sep) for sep in separators), reverse=True)

    sep_counts_1, sep_counts_2 = get_line_seps(f, header=True), get_line_seps(f)
    for (count1, sep1), (count2, sep2) in zip(sep_counts_1, sep_counts_2):
        if sep1 == sep2 and count1 == count2:
            return sep1
    raise ValueError("File contains inconclusive column separators.")

def determine_samplesheet_reader(file_like_obj):
    # https://readxl.tidyverse.org/reference/excel_format.html
    XLSX, XLS = b'PK\x03\x04', b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'
    nibble = file_like_obj.read(4)
    def make_excel_reader(sheet):
        return pd.read_excel(sheet, dtype="object")
    if nibble == XLSX:
        reader = make_excel_reader
    elif nibble + file_like_obj.read(4) == XLS:
        reader = make_excel_reader
    else:
        file_like_obj.seek(0)
        separator = determine_separator(file_like_obj)
        def make_table_reader(sheet, sep=separator):
            return pd.read_table(sheet, dtype="object", sep=sep)
        reader = make_table_reader

    file_like_obj.seek(0)
    return reader


####################################################################################################

def convert_samplesheet(db, file_like_obj, filename, user):
    # Try to read the sample sheet
    try:
        reader = determine_samplesheet_reader(file_like_obj)
        submitted_metadata = reader(file_like_obj)
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
        # Datetimes are converted according to the format string. Empty strings
        # are converted to None aka null, i.e. setting metadata to an empty
        # string value is not possible through the convert API.
        return [ { mdname : None if not row[mdname] else formatted_mrec_value(row[mdname], metadata_datetimefmt[mdname]) for mdname in metadata_names } for _, row in submitted_metadata.iterrows() ]
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

