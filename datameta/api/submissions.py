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

from datetime import datetime
from dataclasses import dataclass
from pyramid.view import view_config
from pyramid.request import Request
from pyramid.httpexceptions import HTTPNoContent, HTTPForbidden, HTTPNotFound
from typing import List
from .. import security, resource, validation, siteid
from ..models import Submission
from ..security import authz
from . import DataHolderBase


@dataclass
class SubmissionBase(DataHolderBase):
    """Base class for Submission communication to OpenApi"""
    metadataset_ids: List[dict]
    file_ids: List[dict]


@dataclass
class SubmissionResponse(SubmissionBase):
    """SubmissionResponse container for OpenApi communication"""
    id: dict
    label: str
    group_id: str
    date_time: datetime

    @classmethod
    def from_submission(cls, submission):

        db_files = [
            mrec.file for mset in submission.metadatasets
            for mrec in mset.metadatumrecords
            if mrec.file_id
        ]

        return cls(
            id = resource.get_identifier(submission),
            label = submission.label,
            metadataset_ids = [ resource.get_identifier(db_mset) for db_mset in submission.metadatasets ],
            file_ids = [ resource.get_identifier(db_file) for db_file in db_files ],
            group_id = submission.group_id,
            date_time = submission.date
        )


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

    # Raises 400 in case of any validation issues
    validation.validate_submission(request, auth_user)

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

    label = request.openapi_validated.body.get("label")
    label = label if label else None  # Convert empty strings to None

    # Raises 400 in case of any validation issues
    fnames, ref_fnames, db_files, db_msets = validation.validate_submission(request, auth_user)

    # Associate the files with the metadata
    for fname, mdatrec in ref_fnames.items():
        mdatrec.file = fnames[fname]

    submission_timestamp = datetime.utcnow()

    # Add a submission
    submission = Submission(
            site_id = siteid.generate(request, Submission),
            label = label,
            date = submission_timestamp,
            metadatasets = list(db_msets.values()),
            group_id = auth_user.group.id
            )
    db.add(submission)
    db.flush()

    return SubmissionResponse(
            id = resource.get_identifier(submission),
            label = label,
            metadataset_ids = [ resource.get_identifier(db_mset) for db_mset in db_msets.values() ],
            file_ids = [ resource.get_identifier(db_file) for db_file in db_files.values() ],
            group_id = auth_user.group_id,
            date_time = submission_timestamp
            )


@view_config(
    route_name      = "submissions_id",
    renderer        = "json",
    request_method  = "GET",
    openapi         = True
)
def get_submission(request: Request) -> SubmissionResponse:
    """Get a submission by ID"""
    auth_user = security.revalidate_user(request)
    db = request.dbsession

    # query targeted submission
    submission = resource.resource_query_by_id(db, Submission, request.matchdict['id']).one_or_none()

    # Check if the metadataset exists
    if not submission:
        raise HTTPNotFound()

    # Check if the user is allowed to view this metadataset
    if not authz.view_group_submissions(auth_user, submission.group_id):
        raise HTTPForbidden()

    return SubmissionResponse.from_submission(submission)
