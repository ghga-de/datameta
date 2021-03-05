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

import datetime
from dataclasses import dataclass
from collections import Counter, defaultdict
from pyramid.view import view_config
from pyramid.request import Request
from pyramid.httpexceptions import HTTPNoContent
from typing import List
from sqlalchemy import and_, or_
from sqlalchemy.orm import joinedload
from .. import errors, siteid, security, resource, linting
from ..models import MetaDatum, MetaDatumRecord, MetaDataSet, Submission, File
from . import DataHolderBase

@dataclass
class SubmissionBase(DataHolderBase):
    """Base class for Submission communication to OpenApi"""
    metadataset_ids: List[str]
    file_ids: List[str]

@dataclass
class SubmissionResponse(SubmissionBase):
    """SubmissionResponse container for OpenApi communication"""
    submission_id:str

def validate_submission_access(db, db_files, db_msets, auth_user):
    """Validates a submission with regard to

    - Entities that cannot be found
    - Entities the user does not have access to

    Raises:
        400 HTTPBadRequest
    """
    # Collect missing files
    val_errors = [ (file_id, None, "Not found") for file_id, db_file in db_files.items() if db_file is None ]
    # Collect authorization issues
    val_errors += [ (file_id, None, "Access denied") for file_id, db_file in db_files.items() if db_file is not None and (db_file.user_id!=auth_user.id or db_file.group_id!=auth_user.group_id) ]

    # Collect missing metadatasets
    val_errors += [ (mset_id, None, "Not found") for mset_id, db_mset in db_msets.items() if db_mset is None ]
    # Collect authorization issues
    val_errors += [ (mset_id, None, "Access denied") for mset_id, db_mset in db_msets.items() if db_mset is not None and (db_mset.user_id!=auth_user.id or db_mset.group_id!=auth_user.group_id) ]

    # If we collected any val_errors so far, raise 400 to avoid exposing internals
    # about data the user should not be able to access
    if val_errors:
        entities, fields, messages = zip(*val_errors)
        raise errors.get_validation_error(messages=messages, fields=fields, entities=entities)

def validate_submission_association(db_files, db_msets):
    """Validates a submission with regard to

    - All submitted files being associated to metadata
    - All files referenced in the metadata being part of the submission
    - All referenced entities have not been submitted before

    Returns (tuple):
        fnames      - A dict mapping file names to database file object
        ref_fnames  - A dict mapping file names referenced by metadatumrecords to the metadatumrecord
        errors      - A list of tuples (entity, field, message) describing the errors that occurred
    """
    errors = []
    # Collect files with no data associated
    errors += [ (file_id, None, "No data uploaded") for file_id, db_file in db_files.items() if db_file.content_uploaded==False ]
    # Collect files which already have other metadata associated
    errors += [ (file_id, None, "Already submitted") for file_id, db_file in db_files.items() if db_file.metadatumrecord is not None ]
    # Collect metadatasets that were already submitted
    errors += [ (mset_id, None, "Already submitted") for mset_id, db_mset in db_msets.items() if db_mset.submission_id is not None ]

    # Collect the file names of the provided files
    fnames = { db_file.name : db_file for db_file in db_files.values() if db_file is not None }
    # Make sure the filenames are unique
    fname_counts = Counter(fnames.keys())
    errors += [ (fname, None, "Filename occurs multiple times among provided files") for fname, count in fname_counts.items() if count > 1 ]

    # Collect the file names referenced by the metadata sets - null values are not considered here
    ref_fnames = { mdatrec.value : mdatrec for mset in db_msets.values() for mdatrec in mset.metadatumrecords if mdatrec.metadatum.isfile and mdatrec.value}
    # Make sure referenced file names are unique
    ref_fname_counts = Counter(ref_fnames.keys())
    errors += [ (ref_fname, None, "Filename occurs multiple times in metadata") for ref_fname, count in ref_fname_counts.items() if count > 1 ]

    # Make sure the files' filenames and the referenced filenames match
    errors += [ (db_file.site_id, None, "File included without reference in metadata") for fname, db_file in fnames.items() if fname not in ref_fnames.keys() ]
    errors += [ (mdatrec.metadataset.site_id, mdatrec.metadatum.name, "File referenced in metadata but not provided") for ref_fname, mdatrec in ref_fnames.items() if ref_fname not in fnames ]

    return fnames, ref_fnames, errors

def validate_submission_uniquekeys(db, db_files, db_msets):
    errors = []

    # Submission unique keys (includes those that are globally unique)
    keys_submission_unique  = [ md.name for md in db.query(MetaDatum).filter(or_(MetaDatum.submission_unique==True, MetaDatum.site_unique==True)) ]
    # Globally unique keys
    keys_site_unique        = [ md.name for md in db.query(MetaDatum).filter(MetaDatum.site_unique==True) ]

    # Validate the set of metadatasets with regard to submission unique key constraints
    for key in keys_submission_unique:
        value_msets = defaultdict(list)
        # Associate all values for that key with the metadatasets it occurs in
        for db_mset in db_msets.values():
            for mdatrec in db_mset.metadatumrecords:
                if mdatrec.metadatum.name==key:
                    value_msets[mdatrec.value].append(db_mset)
        # Reduce to those values that occur in more than one metadatast
        value_msets = { k: v for k, v in value_msets.items() if len(v) > 1 }
        # Produce errrors
        errors += [ (db_mset.site_id, key, "Violation of intra-submission unique constraint") for msets in value_msets.values() for db_mset in msets ]

    # Validate the set of metadatasets with regard to site-wise unique key constraints
    for key in keys_site_unique:
        value_msets = defaultdict(list)
        # Associate all values for that key with the metadatasets it occurs in
        for db_mset in db_msets.values():
            for mdatrec in db_mset.metadatumrecords:
                if mdatrec.metadatum.name==key:
                    value_msets[mdatrec.value].append(db_mset)

        # Query the database for the supplied values
        q = db.query(MetaDatumRecord)\
                .join(MetaDataSet)\
                .join(MetaDatum)\
                .filter(and_(
                    MetaDataSet.submission_id != None,
                    MetaDatum.name==key,
                    MetaDatumRecord.value.in_(value_msets.keys())
                    ))

        db_values = [ rec.value for rec in q ]
        errors += [ (db_mset.site_id, key, "Violation of global unique constraint") for value, msets in value_msets.items() if value in db_values for db_mset in msets ]

    return errors

def validate_submission(request, auth_user):
    db = request.dbsession

    # Collect files, drop duplicates
    db_files = { file_id : resource.resource_query_by_id(db, File, file_id).options(joinedload(File.metadatumrecord)).one_or_none() for file_id in set(request.openapi_validated.body['fileIds']) }
    # Collect metadatasets, drop duplicates
    db_msets = { mset_id : resource.resource_query_by_id(db, MetaDataSet, mset_id).options(joinedload(MetaDataSet.metadatumrecords).joinedload(MetaDatumRecord.metadatum)).one_or_none()
        for mset_id in set(request.openapi_validated.body['metadatasetIds']) }

    # Check for access critical failures
    validate_submission_access(db, db_files, db_msets, auth_user)

    # Validate file and metadata association and submit status
    fnames, ref_fnames, val_errors = validate_submission_association(db_files, db_msets)

    # Convert metadatasets to dictionaries
    msets = { mset_id : { mdatrec.metadatum.name : mdatrec.value for mdatrec in db_mset.metadatumrecords } for mset_id, db_mset in db_msets.items() }

    # Validate every metadataset individually
    for mset_id, mset_values in msets.items():
        mset_errors = linting.validate_metadataset_record(request, mset_values, return_err_message=True, rendered=True)
        val_errors += [ (mset_id, mset_error['field'], mset_error['message']) for mset_error in mset_errors ]

    # Validate unique field constraints
    val_errors += validate_submission_uniquekeys(db, db_files, db_msets)

    # If we collected any val_errors, raise 400
    if val_errors:
        entities, fields, messages = zip(*val_errors)
        raise errors.get_validation_error(messages=messages, fields=fields, entities=entities)

    return fnames, ref_fnames, db_files, db_msets

####################################################################################################

@view_config(
    route_name      = "presubvalidation",
    renderer        = "json",
    request_method  = "POST",
    openapi         = True
)
def post_pre(request: Request) -> HTTPNoContent:
    """Validate a submission without actually creating it.

    Raises:
        400 HTTPBadRequest - The submission is invalid, details are provided in the response body
    """
    # Check authentication and raise 401 if unavailable
    auth_user = security.revalidate_user(request)

    db = request.dbsession

    # Raises 400 in case of any validation issues
    validate_submission(request, auth_user)

    return HTTPNoContent()

####################################################################################################

@view_config(
    route_name      = "submissions",
    renderer        = "json",
    request_method  = "POST",
    openapi         = True
)
def post(request: Request) -> SubmissionResponse:
    """Create a Submission.

    Raises:
        400 HTTPBadRequest - The submission is invalid, details are provided in the response body
    """
    # Check authentication and raise 401 if unavailable
    auth_user = security.revalidate_user(request)

    db = request.dbsession

    # Raises 400 in case of any validation issues
    fnames, ref_fnames, db_files, db_msets = validate_submission(request, auth_user)

    # Associate the files with the metadata
    for fname, mdatrec in ref_fnames.items():
        mdatrec.file = fnames[fname]

    # Add a submission
    submission = Submission(
            date = datetime.datetime.now(),
            metadatasets = list(db_msets.values()),
            site_id = siteid.generate(request, Submission)
            )
    db.add(submission)
    db.flush()

    return SubmissionResponse(
            metadataset_ids = [ db_mset.site_id for db_mset in db_msets.values() ],
            file_ids = [ db_file.site_id for db_file in db_files.values() ],
            submission_id = submission.site_id
            )
