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

from typing import Dict

from sqlalchemy import and_
from sqlalchemy.orm import joinedload

from pyramid.httpexceptions import HTTPOk
from pyramid.request import Request
from pyramid.view import view_config

from ... import security, resource
from ...models import MetaDatum, MetaDataSet, MetaDatumRecord, File
from ..metadatasets import MetaDataSetResponse
from ...utils import get_record_from_metadataset
from ..metadata import get_all_metadata
from ..files import FileResponse


def get_pending_metadatasets(dbsession, user, metadata: Dict[str, MetaDatum]):
    # Query metadatasets that have been no associated submission
    m_sets = dbsession.query(MetaDataSet).filter(and_(
        MetaDataSet.user == user,
        MetaDataSet.submission_id.is_(None))
        ).options(
                joinedload(MetaDataSet.metadatumrecords).joinedload(MetaDatumRecord.metadatum)
                ).all()
    return [
            MetaDataSetResponse(
                id             = resource.get_identifier(m_set),
                record         = get_record_from_metadataset(m_set, metadata),
                file_ids       = { name : None for name, metadatum in metadata.items() if metadatum.isfile },
                user_id        = resource.get_identifier(m_set.user),
                submission_id  = resource.get_identifier(m_set.submission) if m_set.submission else None
                )
            for m_set in m_sets
            ]


def get_pending_files(dbsession, user):
    # Find files that have not yet been associated with metadata
    db_files = dbsession\
            .query(File)\
            .outerjoin(MetaDatumRecord)\
            .filter(and_(File.user_id == user.id, MetaDatumRecord.id.is_(None), File.content_uploaded.is_(True)))\
            .order_by(File.id.desc())
    return [
            FileResponse(
                id                = resource.get_identifier(db_file),
                name              = db_file.name,
                content_uploaded  = db_file.content_uploaded,
                checksum          = db_file.checksum,
                filesize          = db_file.filesize,
                user_id           = resource.get_identifier(db_file.user),
                expires           = db_file.upload_expires.isoformat() if db_file.upload_expires else None
                ) for db_file in db_files
            ]


@view_config(
    route_name      = "pending",
    renderer        = "json",
    request_method  = "GET",
)
def get(request: Request) -> HTTPOk:
    """Get all pending medatasets and files with validation information

    Raises:
        401 HTTPUnauthorized - Authorization not available
    """
    db = request.dbsession
    # Validate authorization or raise HTTPUnauthorized
    auth_user = security.revalidate_user(request)

    # Query metadata fields
    metadata = get_all_metadata(db, include_service_metadata = False)
    mdat_names = list(metadata.keys())
    mdat_names_files = [ mdat_name for mdat_name, mdat in metadata.items() if mdat.isfile ]

    return {
            'metadataKeys'       : mdat_names,
            'metadataKeysFiles'  : mdat_names_files,
            'metadatasets'       : get_pending_metadatasets(db, auth_user, metadata),
            'files'              : get_pending_files(db, auth_user)
            }
