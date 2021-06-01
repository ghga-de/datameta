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

from sqlalchemy.orm import joinedload
from sqlalchemy import or_, and_
from collections import defaultdict, Counter

from . import resource, linting, errors
from .models import File, MetaDataSet, MetaDatumRecord, MetaDatum
from .security import authz
from .api.metadata import get_all_metadata
from .utils import get_record_from_metadataset


def validate_submission_access(db, db_files, db_msets, auth_user):
    """Validates a submission with regard to

    - Entities that cannot be found
    - Entities the user does not have access to

    Raises:
        400 HTTPBadRequest
    """
    # Collect missing files
    val_errors = [
        ({ 'site' : file_id, 'uuid' : file_id }, None, "Not found")
        for file_id, db_file in db_files.items()
        if db_file is None
    ]
    # Collect authorization issues
    val_errors += [
        ({ 'site' : file_id, 'uuid' : file_id }, None, "Access denied")
        for file_id, db_file in db_files.items()
        if db_file is not None and not authz.submit_file(auth_user, db_file)
    ]

    # Collect missing metadatasets
    val_errors += [
        ({ 'site' : mset_id, 'uuid' : mset_id }, None, "Not found")
        for mset_id, db_mset in db_msets.items()
        if db_mset is None
    ]
    # Collect authorization issues
    val_errors += [
        ({ 'site' : mset_id, 'uuid' : mset_id }, None, "Access denied")
        for mset_id, db_mset in db_msets.items()
        if db_mset is not None and not authz.submit_mset(auth_user, db_mset) ]

    # If we collected any val_errors so far, raise 400 to avoid exposing internals
    # about data the user should not be able to access
    if val_errors:
        entities, fields, messages = zip(*val_errors)
        raise errors.get_validation_error(messages=messages, fields=fields, entities=entities)


def validate_submission_association(db_files, db_msets, ignore_submitted_metadatasets = False):
    """Validates a submission with regard to

    - All submitted files being associated to metadata
    - All files referenced in the metadata being part of the submission
    - All referenced entities have not been submitted before

    Returns (tuple):
        f_names_obj - A dict mapping file names to database file object
        ref_fnames  - A dict mapping file names referenced by metadatumrecords to the metadatumrecord
        errors      - A list of tuples (entity, field, message) describing the errors that occurred
    """
    errors = []
    # Collect files with no data associated
    errors += [ (db_file, None, "No data uploaded") for file_id, db_file in db_files.items() if not db_file.content_uploaded ]
    # Collect files which already have other metadata associated
    errors += [ (db_file, None, "Already submitted") for file_id, db_file in db_files.items() if db_file.metadatumrecord is not None ]
    # Collect metadatasets that were already submitted
    if not ignore_submitted_metadatasets:
        errors += [ (db_mset, None, "Already submitted") for mset_id, db_mset in db_msets.items() if db_mset.submission_id is not None ]

    # Collect the file names of the provided files
    f_names_obj = defaultdict(list)
    for db_file in db_files.values():
        if db_file is not None:
            f_names_obj[db_file.name].append(db_file)

    # Make sure the filenames are unique
    for fname, db_objs in f_names_obj.items():
        if len(db_objs) > 1:
            errors += [ (db_file, None, "Filename occurs multiple times among provided files") for db_file in db_objs ]

    # Collect the file names referenced by the metadata sets - null values are
    # not considered here, neither are records for which the file has already
    # been linked (this case can occur when this function is called during a
    # service execution)
    mdat_fnames_obj = defaultdict(list)
    for mset in db_msets.values():
        for mdatrec in mset.metadatumrecords:
            if mdatrec.value is not None and mdatrec.metadatum.isfile and mdatrec.file_id is None:
                mdat_fnames_obj[mdatrec.value].append(mdatrec)

    ref_fnames = { mdatrec.value : mdatrec for mset in db_msets.values() for mdatrec in mset.metadatumrecords if mdatrec.metadatum.isfile and mdatrec.value and mdatrec.file_id is None}
    # Make sure referenced file names are unique
    ref_fname_counts = Counter(mdatrec.value for mdatrecs in mdat_fnames_obj.values() for mdatrec in mdatrecs)
    errors += [ (mdatrec.metadataset, mdatrec.metadatum.name, "Filename occurs multiple times in metadata")
            for ref_fname, count in ref_fname_counts.items() if count > 1
            for mdatrec in mdat_fnames_obj[ref_fname]]

    # Make sure the files' filenames and the referenced filenames match
    errors += [ (db_file, None, "File included without reference in metadata") for db_file in db_files.values() if db_file.name not in ref_fnames.keys() ]
    errors += [ (mdatrec.metadataset, mdatrec.metadatum.name, "Referenced file not provided") for ref_fname, mdatrec in ref_fnames.items() if ref_fname not in f_names_obj ]

    return f_names_obj, ref_fnames, errors


def validate_submission_uniquekeys(db, db_files, db_msets):
    errors = []

    # Submission unique keys (includes those that are globally unique)
    keys_submission_unique  = [ md.name for md in db.query(MetaDatum).filter(or_(MetaDatum.submission_unique.is_(True), MetaDatum.site_unique.is_(True))) ]
    # Globally unique keys
    keys_site_unique        = [ md.name for md in db.query(MetaDatum).filter(MetaDatum.site_unique.is_(True)) ]

    # Validate the set of metadatasets with regard to submission unique key constraints
    for key in keys_submission_unique:
        value_msets = defaultdict(list)
        # Associate all values for that key with the metadatasets it occurs in
        for db_mset in db_msets.values():
            for mdatrec in db_mset.metadatumrecords:
                if mdatrec.metadatum.name == key:
                    value_msets[mdatrec.value].append(db_mset)
        # Reduce to those values that occur in more than one metadatast
        value_msets = { k: v for k, v in value_msets.items() if len(v) > 1 }
        # Produce errrors
        errors += [ (db_mset, key, "Violation of intra-submission unique constraint") for msets in value_msets.values() for db_mset in msets ]

    # Validate the set of metadatasets with regard to site-wise unique key constraints
    for key in keys_site_unique:
        value_msets = defaultdict(list)
        # Associate all values for that key with the metadatasets it occurs in
        for db_mset in db_msets.values():
            for mdatrec in db_mset.metadatumrecords:
                if mdatrec.metadatum.name == key:
                    value_msets[mdatrec.value].append(db_mset)

        # Query the database for the supplied values
        q = db.query(MetaDatumRecord)\
                .join(MetaDataSet)\
                .join(MetaDatum)\
                .filter(and_(
                    MetaDataSet.submission_id.isnot(None),
                    MetaDatum.name == key,
                    MetaDatumRecord.value.in_(value_msets.keys())
                    ))

        db_values = [ rec.value for rec in q ]
        errors += [ (db_mset, key, "Violation of global unique constraint") for value, msets in value_msets.items() if value in db_values for db_mset in msets ]

    return errors


def validate_submission(request, auth_user):
    db = request.dbsession

    # Collect files, drop duplicates
    db_files = { file_id : resource.resource_query_by_id(db, File, file_id).options(joinedload(File.metadatumrecord)).one_or_none() for file_id in set(request.openapi_validated.body['fileIds']) }
    # Collect metadatasets, drop duplicates
    db_msets = { mset_id : resource.resource_query_by_id(db, MetaDataSet, mset_id).options(joinedload(MetaDataSet.metadatumrecords).joinedload(MetaDatumRecord.metadatum)).one_or_none()
        for mset_id in set(request.openapi_validated.body['metadatasetIds']) }

    if not db_files and not db_msets:
        raise errors.get_validation_error(messages=["Neither data nor metadata provided in submission."])

    # Check for access critical failures
    validate_submission_access(db, db_files, db_msets, auth_user)

    # Validate file and metadata association and submit status
    fnames, ref_fnames, val_errors = validate_submission_association(db_files, db_msets)

    # Get all non-service metadata definitions
    metadata = get_all_metadata(db, include_service_metadata=False)

    # Convert metadatasets to dictionaries
    msets = { mset_id : get_record_from_metadataset(db_mset, metadata, False) for mset_id, db_mset in db_msets.items() }

    # Validate every metadataset individually
    for mset_id, mset_values in msets.items():
        mset_errors = linting.validate_metadataset_record(metadata, mset_values, return_err_message=True, rendered=True)
        val_errors += [ (db_msets[mset_id], mset_error['field'], mset_error['message']) for mset_error in mset_errors ]

    # Validate unique field constraints
    val_errors += validate_submission_uniquekeys(db, db_files, db_msets)

    # If we collected any val_errors, raise 400
    if val_errors:
        entities, fields, messages = zip(*val_errors)
        raise errors.get_validation_error(messages=messages, fields=fields, entities=entities)

    # Given that validation hasn't failed, we know that file names are unique. Flatten the dict.
    fnames = { k : v[0] for k, v in fnames.items() }

    return fnames, ref_fnames, db_files, db_msets
