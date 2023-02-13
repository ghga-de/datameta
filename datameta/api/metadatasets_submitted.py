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
from pyramid.httpexceptions import HTTPForbidden, HTTPNotFound, HTTPNoContent, HTTPInternalServerError
from pyramid.view import view_config
from pyramid.request import Request
from typing import List
from ..models import MetaDataSet, MetaDatumRecord
from ..security import authz
from ..resource import resource_by_id
from . import DataHolderBase
from .. import errors
from ..storage import rm

log = logging.getLogger(__name__)

"""
"""


@dataclass
class MetaDataSetSubmittedDeleteBase(DataHolderBase):
    """Base class for File communication to OpenApi"""
    id: str


@dataclass
class  MetaDataSetSubmittedDeleteResponse(MetaDataSetSubmittedDeleteBase):
    """"""
    pass


@view_config(
    route_name="metadatasets_submitted_id",
    renderer='json',
    request_method="DELETE",
    openapi=True
)
def delete_metadataset(request: Request) -> HTTPNoContent:
    auth_user = authz.revalidate_user(request)
    db_session = request.dbsession
    metadataset_id = request.matchdict['id']
    target_metadataset = resource_by_id(db_session, MetaDataSet, metadataset_id)

    #
    # Checks
    #

    # Authorization
    # 401
    if not authz.delete_submitted_metadataset(auth_user):
        raise HTTPForbidden()

    # Metadataset exists
    # 404
    if not target_metadataset:
        raise HTTPNotFound()

    # Only operate on submitted metadatasets
    # 403
    if not target_metadataset.submission:
        raise errors.get_not_modifiable_error()

    # Get files
    target_metadatarecords_files: List[MetaDatumRecord] = [
        metadatum_record
        for metadatum_record in target_metadataset.metadatumrecords
        if metadatum_record.metadatum.isfile
    ]

    #
    # Delete the files
    #
    if target_metadatarecords_files:
        for metadatum_record in target_metadatarecords_files:
            try:
                rm(request=request, file_id=metadatum_record.file_id)
            except Exception as e:
                raise HTTPInternalServerError(json_body={'error': str(e)})

    #
    # Delete the metadataset
    #

    db_session.delete(target_metadataset)

    #
    # Submission has no other metadatasets
    #

    # not implemented yet

    #
    # Service executions?
    #

    # not implemented yet

    return MetaDataSetSubmittedDeleteResponse(
        metadataset_id=metadataset_id,
    )
