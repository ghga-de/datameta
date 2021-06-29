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

from pyramid.view import view_config
from pyramid.request import Request
from typing import List
from dataclasses import dataclass
from . import DataHolderBase
from .. import models
from ..models import Group
from .. import security, errors
from ..security import authz
from ..resource import resource_by_id, resource_query_by_id, get_identifier
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import IntegrityError

from pyramid.httpexceptions import HTTPNoContent, HTTPForbidden, HTTPNotFound


@dataclass
class GroupResponseElement(DataHolderBase):
    """Class for Group Information Request communication to OpenApi"""
    id: dict
    name: str


class GroupSubmissions:
    """GroupSubmissions container for OpenApi communication"""
    submissions: List[dict]

    def __init__(self, request: Request, group_id: str):
        db = request.dbsession
        group = resource_query_by_id(db, models.Group, group_id).options(
            joinedload(
                Group.submissions
            ).joinedload(
                models.Submission.metadatasets
            ).joinedload(
                models.MetaDataSet.metadatumrecords
            ).joinedload(
                models.MetaDatumRecord.metadatum
            )
        ).one_or_none()

        self.submissions = [
            {
                "id": get_identifier(sub),
                "label": sub.label,
                "metadatasetIds": [
                    get_identifier(mset)
                    for mset in sub.metadatasets
                ],
                "fileIds": self._get_file_ids_of_submission(sub)
            }
            for sub in group.submissions
        ]

    def _get_file_ids_of_submission(self, submission: models.Submission):
        file_ids = []
        for mset in submission.metadatasets:
            file_records = [
                rec
                for rec in mset.metadatumrecords
                if rec.metadatum.isfile and rec.value
            ]
            file_ids.extend(
                [get_identifier(rec.file) for rec in file_records]
            )
        return file_ids

    def __json__(self, requests: Request) -> List[dict]:
        return self.submissions


@view_config(
    route_name="groups_id_submissions",
    renderer='json',
    request_method="GET",
    openapi=True
)
def get_all_submissions(request: Request) -> GroupSubmissions:
    """Get all submissions of a given group."""
    auth_user = security.revalidate_user(request)
    group_id = request.matchdict["id"]

    db = request.dbsession
    target_group = resource_by_id(db, Group, group_id)

    if target_group is None:
        raise HTTPForbidden()  # 403 Group ID not found, hidden from the user intentionally

    # check if user is part of the target group:
    if not authz.view_group_submissions(auth_user, group_id):
        raise HTTPForbidden()

    return GroupSubmissions(
        request=request,
        group_id=group_id
    )


@dataclass
class ChangeGroupName(DataHolderBase):
    """Class for Group Name Change communication to OpenApi"""
    group_id: str
    new_group_name: str


@view_config(
    route_name="groups_id",
    renderer="json",
    request_method="GET",
    openapi=True
)
def get(request: Request):

    # Authenticate the user
    auth_user = security.revalidate_user(request)

    group_id = request.matchdict["id"]
    db = request.dbsession

    # Get the targeted user
    target_group = resource_by_id(db, Group, group_id)

    if target_group is None:
        raise HTTPNotFound()

    if not authz.view_group(auth_user, target_group):
        raise HTTPForbidden()

    return GroupResponseElement(
        id              =   get_identifier(target_group),
        name            =   target_group.name,
    )


@view_config(
    route_name="groups_id",
    renderer='json',
    request_method="PUT",
    openapi=True
)
def put(request: Request):
    """Change the name of the group"""

    group_id = request.matchdict["id"]
    new_group_name = request.openapi_validated.body["name"]
    db = request.dbsession

    # Authenticate the user
    auth_user = security.revalidate_user(request)

    target_group = resource_by_id(db, Group, group_id)

    if target_group is None:
        raise HTTPForbidden()  # 403 Group ID not found, hidden from the user intentionally

    if authz.update_group_name(auth_user):
        try:
            target_group.name = new_group_name
            db.flush()
        except IntegrityError:
            raise errors.get_validation_error(["A group with that name already exists."])

        return HTTPNoContent()
    raise HTTPForbidden()  # 403 Not authorized to change this group name
