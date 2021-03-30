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

from datameta.models import MetaDataSet, MetaDatum, File
from .errors import get_validation_error
from sqlalchemy import and_
from pyramid.request import Request

from collections import Counter
import re
import datetime

def lint_pending_msets(request, user, mset_ids = None):
    """Performs linting on the pending metadatasets for a given user. Optionally filter those
    metadatasets for only those specified in the ID list."""
    db = request.dbsession

    # Query metadata fields
    mdats = db.query(MetaDatum).order_by(MetaDatum.order).all()
    mdat_names = [ mdat.name for mdat in mdats ]
    mdat_names_files = [ mdat.name for mdat in mdats if mdat.isfile ]

    # Obtain all pending metadatasets
    if mset_ids is None:
        mdatasets = db.query(MetaDataSet).filter(and_(
            MetaDataSet.submission_id==None,
            MetaDataSet.user_id==user.id))
    # Or obtain all pending metadatasets that match the specified mset ids
    else:
        mdatasets = db.query(MetaDataSet).filter(and_(
            MetaDataSet.submission_id==None,
            MetaDataSet.user_id==user.id,
            MetaDataSet.id.in_(mset_ids)))

    # Create result structure
    linting_report = { mdataset.id : [] for mdataset in mdatasets }

    # Obtain all corresponding metadata records
    mdatrecs = [ mdatrec for mdataset in mdatasets for mdatrec in mdataset.metadatumrecords ]

    # Keep track of file names
    file_names        = [ mdatrec.value for mdatrec in mdatrecs if mdatrec.metadatum.isfile ]
    file_names_red    = [ file_name for file_name, count in Counter(file_names).items() if count > 1 ]
    # Keep track of already uploaded files...
    uploaded_files = db.query(File).filter(and_(File.user_id==user.id, File.metadatumrecord == None))
    uploaded_files = { file.name : file for file in uploaded_files }
    # ... and their association with file names
    file_pairs = []
    for mdatrec in mdatrecs:
        metadatum = mdatrec.metadatum
        mdset_id  = mdatrec.metadataset.id
        value     = mdatrec.value
        # If this metadatum is mandatory or has been specified "voluntarily" it
        # has to undergo validation
        if metadatum.mandatory or value != "":
            # Count file name occurrences and report duplicates
            if metadatum.isfile and value in file_names_red:
                linting_report[mdset_id].append({
                    'field' : metadatum.name,
                    'type' : 'custom',
                    'error' : f"Filename '{value}' is specified multiple times in the sample sheet."
                    })
            # Check for files that have not yet been uploaded
            if metadatum.isfile and value not in uploaded_files.keys():
                linting_report[mdset_id].append({
                    'field' : metadatum.name,
                    'type' : 'nofile',
                    })
            elif metadatum.isfile:
                file_pairs.append((mdatrec, uploaded_files[value]))
            # Check if the regexp pattern matches
            if metadatum.regexp and re.match(metadatum.regexp, value) is None:
                linting_report[mdset_id].append({
                    'field' : metadatum.name,
                    'type' : 'custom',
                    'error' : metadatum.short_description
                    })
            # Check if the datetime was correctly parsed or specified at all
            if metadatum.datetimefmt and value=="":
                linting_report[mdset_id].append({
                    'field' : metadatum.name,
                    'type' : 'custom',
                    'error' : "The field was either empty or it could not be parsed as a valid date / time"
                    })

    # Return those metadatasets that passed linting, the record-file associations and the linting
    # report for the failed records
    good_sets = [ mdataset for mdataset in mdatasets if not linting_report[mdataset.id] ]
    return good_sets, file_pairs, linting_report


def validate_metadataset_record(
    request:Request,
    record:dict, 
    return_err_message:bool=False,
    rendered:bool=False # set to true if values have already
                        # been rendered (e.g. datetime fields
                        # already in isoformat) 
):
    """Validate single metadataset in isolation"""
    errors = [] # list of error
                # empty means success

    # get all metadatum fields:
    db = request.dbsession
    mdats_query = db.query(MetaDatum).order_by(MetaDatum.order).all()
    mdats = { mdat.name: mdat for mdat in mdats_query }
    
    for name, mdat in mdats.items():
        
        # check if mdat is present in record dict
        # if not and mdat is mandatory, throw an error:
        if name not in record:
            if mdat.mandatory:
                errors.append({
                    "message": "field was not specified but is mandatory",
                    "field": name
                })
            continue
        
        value = record[name]

        # if value is none but mandatory,
        # throw and error, moreover, if the value is none
        # but not mandatory skip the following checks:
        if value is None:
            if mdat.mandatory:
                errors.append({
                    "message": "field value was null, but the field is mandatory",
                    "field": name
                })
            continue

        # check if values are of allowed types:
        # (all values will be stringified later)
        if not isinstance(value, str):
            errors.append({
                "message": "field value must be a string.",
                "field": name
            })

        # Check if the regexp pattern matches
        if mdat.regexp and re.match(mdat.regexp, value) is None:
            errors.append({
                "message": mdat.short_description,
                "field": name
            })
            continue
        
        # check if datetime formats are matched
        if mdat.datetimefmt:
            try:
                if rendered:
                    # check if value is in isoformat:
                    _ = datetime.datetime.fromisoformat(value)
                else:
                    # check whether value matches the datetime format
                    _ = datetime.datetime.strptime(
                        value, mdat.datetimefmt
                    ).isoformat()
            except (ValueError, TypeError):
                errors.append({
                    "message": "The field could not be parsed as a valid date / time",
                    "field": name
                })
                continue   
    
    # check if any of the record fields has no corresponding MetaDatum object:
    mdats_set = set(mdats.keys())
    record_set = set(record.keys())
    if not record_set.issubset(mdats_set):
        for field in record_set.difference(mdats_set):
            errors.append({
                "message": "The field was not expected.",
                "field": field
            })
            
    # return the error messages
    # or raise validation errors
    if return_err_message:
        return errors
    elif len(errors) > 0:
        messages = [err["message"] for err in errors]
        fields = [
            err["field"] if "field" in err else None 
            for err in errors
        ]
        raise get_validation_error(messages, fields)
