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

from datameta.models import MetaDataSet, MetaDatum, File
from .errors import get_validation_error
from sqlalchemy import and_
from pyramid.request import Request

from collections import Counter
import re
import datetime

def validate_metadataset_record(
    request:Request,
    record:dict, 
    return_err_message:bool=False,
    rendered:bool=False # set to true if values have already
                        # been rendered (e.g. datetime fields
                        # already in isoformat) 
):
    """Validate single metadataset in isolation"""
    errors = [] # list of errors
                # empty means success

    # get all metadatum fields:
    db = request.dbsession
    mdats_query = db.query(MetaDatum).order_by(MetaDatum.order).all()
    mdats = { mdat.name: mdat for mdat in mdats_query }

    if mdats.get("isFile") and not mdats.get("name"):
        errors.append({
            "message": "file names cannot be empty.",
            "field": "name"
        })

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
    elif errors:
        messages = [err["message"] for err in errors]
        fields = [
            err["field"] if "field" in err else None
            for err in errors
        ]
        raise get_validation_error(messages, fields)
