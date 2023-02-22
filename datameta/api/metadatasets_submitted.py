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

import logging
from dataclasses import dataclass
from typing import List

from pyramid.httpexceptions import (HTTPInternalServerError, HTTPNotFound,
                                    HTTPUnauthorized)
from pyramid.request import Request
from pyramid.view import view_config

from .. import errors, security
from ..models import MetaDataSet, MetaDatumRecord
from ..resource import get_identifier, resource_by_id
from ..security import authz
from ..storage import rm
from . import DataHolderBase

log = logging.getLogger(__name__)

"""
This module contains API enpoints for submitted metadatasets.
"""


@dataclass
class MetaDataSetSubmittedDeleteBase(DataHolderBase):
    """Base class for MetaDataSetSubmittedDelete API response bodies"""
    metadataset_id: str


@dataclass
class  MetaDataSetSubmittedDeleteResponse(MetaDataSetSubmittedDeleteBase):
    """Response class for MetaDataSetSubmittedDelete API response bodies"""
    file_ids: List[str]


@view_config(
    route_name="metadatasets_submitted_id",
    renderer='json',
    request_method="DELETE",
    openapi=True
)
def delete_submitted_metadataset(request: Request) -> MetaDataSetSubmittedDeleteResponse:
    """"Delete a submitted metadataset and all associated files"""
    auth_user = security.revalidate_user(request)
    # Authorization 401
    if not authz.delete_submitted_metadataset(auth_user):
        raise HTTPUnauthorized()

    db_session = request.dbsession
    metadataset_id = request.matchdict['id']
    target_metadataset = resource_by_id(db_session, MetaDataSet, metadataset_id)

    # 404
    if not target_metadataset:
        raise HTTPNotFound()

    # Only ubmitted metadatasets 403
    if not target_metadataset.submission:
        raise errors.get_not_modifiable_error()

    # Get files
    target_metadatarecords_files: List[MetaDatumRecord] = [
        metadatum_record
        for metadatum_record in target_metadataset.metadatumrecords
        if metadatum_record.metadatum.isfile and metadatum_record.value
    ]
    # Get the File identifiers
    target_metadatarecords_files_ids: List[str] = [
        get_identifier(metadatum_record.file)
        for metadatum_record in target_metadatarecords_files
    ]

    #
    # Delete the files from storage and the File objects (File is parent of MetaDatumRecord)
    #
    if target_metadatarecords_files:
        for metadatum_record in target_metadatarecords_files:
            try:
                log.info("Deleting file.", extra={"file_site_id": metadatum_record.file.site_id, "user_site_id": auth_user.site_id})
                rm(request=request, storage_path=metadatum_record.file.storage_uri)
                db_session.delete(metadatum_record.file)
            except FileNotFoundError as e:
                log.warning("File not found in storage. Skipping deletion.", extra={"file_site_id": metadatum_record.file.site_id, "user_site_id": auth_user.site_id})
                raise HTTPInternalServerError(json_body={'error': str(e)})
            except Exception as e:
                raise HTTPInternalServerError(json_body={'error': str(e)})

    #
    # Delete the metadataset
    #
    log.info("Deleting metadataset.", extra={"metadataset_id": metadataset_id, "user_site_id": auth_user.site_id})
    db_session.delete(target_metadataset)

    #
    # TODO: Submission has no other metadatasets
    #

    return MetaDataSetSubmittedDeleteResponse(
        metadataset_id=get_identifier(target_metadataset),
        file_ids=target_metadatarecords_files_ids,
    )
