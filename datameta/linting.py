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
            MetaDataSet.user_id==user.id,
            MetaDataSet.group_id==user.group_id))
    # Or obtain all pending metadatasets that match the specified mset ids
    else:
        mdatasets = db.query(MetaDataSet).filter(and_(
            MetaDataSet.submission_id==None,
            MetaDataSet.user_id==user.id,
            MetaDataSet.group_id==user.group_id,
            MetaDataSet.id.in_(mset_ids)))

    # Create result structure
    linting_report = { mdataset.id : [] for mdataset in mdatasets }

    # Obtain all corresponding metadata records
    mdatrecs = [ mdatrec for mdataset in mdatasets for mdatrec in mdataset.metadatumrecords ]

    # Keep track of file names
    file_names        = [ mdatrec.value for mdatrec in mdatrecs if mdatrec.metadatum.isfile ]
    file_names_red    = [ file_name for file_name, count in Counter(file_names).items() if count > 1 ]
    # Keep track of already uploaded files...
    uploaded_files = db.query(File).filter(and_(File.user_id==user.id, File.group_id==user.group_id, File.metadatumrecord == None))
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
                    'error' : metadatum.lintmessage
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
    
    for name, value in record.items():
        
        # check if the name appears in the metadatum list
        if not name in mdats.keys():
            errors.append({
                "message": (
                    f"field with name \"name\""
                    "is not allowed"
                ),
                "field": name
            })
            continue
        mdat = mdats[name]
        
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
                "message": mdat.lintmessage,
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
    
    # Check if all mandatory fields exist:
    mdats_mandatory = {name for name, mdat in mdats.items() if mdat.mandatory}
    rec_names = set(record.keys())
    if not mdats_mandatory.issubset(rec_names):
        errors.append({
            "message": "The record is missing mandatory fields.",
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
