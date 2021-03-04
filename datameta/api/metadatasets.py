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

from dataclasses import dataclass
from pyramid.httpexceptions import HTTPForbidden, HTTPNotFound
from pyramid.view import view_config
from pyramid.request import Request
from typing import Optional, Dict
from ..linting import validate_metadataset_record
from .. import security, siteid, models
import datetime
from ..resource import resource_by_id

@dataclass
class MetaDataSetResponse:
    """MetaDataSetResponse container for OpenApi communication"""
    record: dict
    group_id: str
    user_id: str
    metadataset_id: str
    submission_id: Optional[str] = None

    def __json__(self, request: Request) -> dict:
        return {
                "record": self.record,
                "groupId": self.group_id,
                "userId": self.user_id,
                "submissionId": self.submission_id,
                "metaDataSetId": self.metadataset_id,
            }


def render_record_values(mdatum:Dict[str, models.MetaDatum], record:dict) -> dict:
    """Renders values of a metadataset record"""
    for field in record:
        if mdatum[field].datetimefmt:
            record[field] = datetime.datetime.strptime(
                    record[field], 
                    mdatum[field].datetimefmt
                ).isoformat()

    return(record)


def get_record_from_metadataset(mdata_set=models.MetaDataSet) -> dict:
    """ Construct a dict containing all records of that MetaDataSet"""
    return {
        rec.metadatum.name: rec.value
        for rec in mdata_set.metadatumrecords
    }


@view_config(
    route_name="metadatasets", 
    renderer='json', 
    request_method="POST", 
    openapi=True
)
def post(request:Request) -> MetaDataSetResponse:
    """Create new metadataset"""
    auth_user = security.revalidate_user(request)
    record = request.openapi_validated.body["record"]
    # prevalidate (raises 400 in case of validation failure):
    validate_metadataset_record(request, record)
    
    # render records according to MetaDatum constraints
    db = request.dbsession
    mdatum_query = db.query(models.MetaDatum).order_by(
        models.MetaDatum.order
    ).all()
    mdatum = {mdat.name: mdat for mdat in mdatum_query }
    record = render_record_values(mdatum, record)

    # construct new MetaDataSet:
    mdata_set = models.MetaDataSet(
        site_id = siteid.generate(request, models.MetaDataSet),
        user_id = auth_user.id,
        group_id = auth_user.group.id,
        submission_id = None
    )
    db.add(mdata_set)
    db.flush()

    # construct new MetaDatumRecords
    for name, value in record.items():
        mdatum_rec = models.MetaDatumRecord(
            metadatum_id = mdatum[name].id,
            metadataset_id = mdata_set.id,
            file_id = None,
            value = value
        )
        db.add(mdatum_rec)

    return MetaDataSetResponse(
        metadataset_id=mdata_set.site_id,
        record=record,
        group_id=mdata_set.group.site_id,
        user_id=mdata_set.user.site_id,
        submission_id=mdata_set.submission_id,
    )
        

@view_config(
    route_name="metadatasets_id", 
    renderer='json', 
    request_method="GET", 
    openapi=True
)
def get_metadataset(request:Request) -> MetaDataSetResponse:
    """Create new metadataset"""
    auth_user = security.revalidate_user(request)
    db = request.dbsession
    mdata_set = resource_by_id(db, models.MetaDataSet, request.matchdict['id'])

    if not mdata_set:
        raise HTTPNotFound()
    
    # check if user is in the group of that metadataset:
    if not auth_user.group.id == mdata_set.group.id:
        raise HTTPForbidden()

    return MetaDataSetResponse(
        metadataset_id=mdata_set.site_id,
        record=get_record_from_metadataset(mdata_set),
        group_id=mdata_set.group.site_id,
        user_id=mdata_set.user.site_id,
        submission_id=mdata_set.submission_id,
    )
