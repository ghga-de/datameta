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

from sqlalchemy import and_
from sqlalchemy.orm import joinedload

from pyramid.httpexceptions import HTTPOk
from pyramid.request import Request
from pyramid.view import view_config

from ... import security, resource
from ...models import MetaDatum, MetaDataSet, MetaDatumRecord, File
from ..metadatasets import MetaDataSetResponse, get_record_from_metadataset
from ..files import FileResponse
from .convert import formatted_mrec_value

####################################################################################################

def get_pending_metadatasets(dbsession, user):
    # Query metadatasets that have been no associated submission
    m_sets = dbsession.query(MetaDataSet).filter(and_(
        MetaDataSet.user==user,
        MetaDataSet.group==user.group,
        MetaDataSet.submission==None)
        ).options(joinedload(MetaDataSet.metadatumrecords).joinedload(MetaDatumRecord.metadatum)).all()
    return [
            MetaDataSetResponse(
                id             = resource.get_identifier(m_set),
                record         = get_record_from_metadataset(m_set),
                group_id       = resource.get_identifier(m_set.group),
                user_id        = resource.get_identifier(m_set.user),
                submission_id  = resource.get_identifier(m_set.submission) if m_set.submission else None
                )
            for m_set in m_sets
            ]

####################################################################################################

def get_pending_files(dbsession, user):
    # Find files that have not yet been associated with metadata
    db_files = dbsession.query(File).filter(and_(File.user_id==user.id, File.group_id==user.group_id, File.metadatumrecord==None, File.content_uploaded==True)).order_by(File.id.desc())
    return [
            FileResponse(
                id                = resource.get_identifier(db_file),
                name              = db_file.name,
                content_uploaded  = db_file.content_uploaded,
                checksum          = db_file.checksum,
                filesize          = db_file.filesize,
                user_id           = resource.get_identifier(db_file.user),
                group_id          = resource.get_identifier(db_file.group),
                expires           = db_file.upload_expires.isoformat() if db_file.upload_expires else None
                ) for db_file in db_files
            ]

####################################################################################################

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
    mdats = db.query(MetaDatum).order_by(MetaDatum.order).all()
    mdat_names = [ mdat.name for mdat in mdats ]
    mdat_names_files = [ mdat.name for mdat in mdats if mdat.isfile ]

    return {
            'metadataKeys'       : mdat_names,
            'metadataKeysFiles'  : mdat_names_files,
            'metadatasets'       : get_pending_metadatasets(db, auth_user),
            'files'              : get_pending_files(db, auth_user)
            }
