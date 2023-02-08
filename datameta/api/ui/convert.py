# Copyright 2021 Universität Tübingen, DKFZ and EMBL for the German Human Genome-Phenome Archive (GHGA)
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

from pyramid.httpexceptions import HTTPOk
from pyramid.request import Request
from pyramid.view import view_config
import webob
import logging
import csv

import pandas as pd

from ... import security, samplesheet, errors
from ...utils import formatted_mrec_value_str
from ..metadata import get_all_metadata

log = logging.getLogger(__name__)


def get_samplesheet_reader(file_like_obj):
    """Given a file with tabular data which is either in delimited plain text
    format or in XLS(X) format, returns a function capable of reading the file
    and returning a pandas.DataFrame"""
    # https://readxl.tidyverse.org/reference/excel_format.html
    xlsx_sig    = b'PK\x03\x04'
    xls_sig     = b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'
    magic_bytes = file_like_obj.read(8)

    file_like_obj.seek(0)

    if magic_bytes.startswith(xlsx_sig) or magic_bytes.startswith(xls_sig):
        def create_excel_reader(sheet):
            return pd.read_excel(sheet, dtype="object")
        return create_excel_reader
    else:
        dialect = csv.Sniffer().sniff(file_like_obj.read(1024).decode())

        def create_table_reader(sheet, sep=dialect.delimiter):
            return pd.read_table(sheet, dtype="object", sep=sep)
        file_like_obj.seek(0)
        return create_table_reader


####################################################################################################


def convert_samplesheet(db, file_like_obj, filename, user):
    # Try to read the sample sheet
    try:
        reader = get_samplesheet_reader(file_like_obj)
        submitted_metadata = reader(file_like_obj)
    except Exception as e:
        log.info("Sample sheet conversion failed.", extra={"file_name": filename, "error": e})
        raise samplesheet.SampleSheetReadError("Unable to parse the sample sheet.")

    # Query column names that we expect to see in the sample sheet (intra-submission duplicates)
    metadata               = get_all_metadata(db, include_service_metadata = False)
    metadata_names         = list(metadata.keys())
    metadata_datetimefmt   = { datum.name : datum.datetimefmt for datum in metadata.values() }

    missing_columns  = [ metadata_name for metadata_name in metadata_names if metadata_name not in submitted_metadata.columns ]
    if missing_columns:
        raise samplesheet.SampleSheetReadError(f"Missing columns: {', '.join(missing_columns)}.")

    # Limit the sample sheet to the columns of interest and drop duplicates
    submitted_metadata = submitted_metadata[metadata_names].drop_duplicates()

    # Convert all data to strings
    samplesheet.string_conversion(submitted_metadata, list(metadata.values()))

    try:
        # Datetimes are converted according to the format string. Empty strings
        # are converted to None aka null, i.e. setting metadata to an empty
        # string value is not possible through the convert API.
        return [ { mdname : None if not row[mdname] else formatted_mrec_value_str(row[mdname], metadata_datetimefmt[mdname]) for mdname in metadata_names } for _, row in submitted_metadata.iterrows() ]
    except Exception as e:
        log.error("Unexpected error during sample sheet conversion.", extra={"file_name": filename, "error": e})
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
        log.warning("Unable to read sample sheet.", extra={"file_name": input_file.filename, "error": e})
        raise errors.get_validation_error(messages = [ str(e) ])
