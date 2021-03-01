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
from pyramid.view import view_config
from pyramid.request import Request
from typing import Optional, Dict
from .. import models

# For Developers: if needed change the dataclasses to
# regular classes and supply custom __init__ functions
# (for instance if create of that class object should
# also trigger creation of the respective db model)

@dataclass
class MetaDataSets:
    """MetaDataSets container for OpenApi communication"""
    records: dict
    group_id: str
    user_id: str
    metadataset_id: str
    submission_id: Optional[str] = None

    def __json__(self, request: Request) -> dict:
        return {
                "records": self.records,
                "groupId": self.group_id,
                "userId": self.user_id,
                "submissionId": self.submission_id,
                "metaDataSetId": self.metadataset_id,
            }


@view_config(
    route_name="metadatasets", 
    renderer='json', 
    request_method="POST", 
    openapi=True
)
def post(request:Request) -> MetaDataSets:
    """Create new metadataset"""
    pass
    return {}
    

@view_config(
    route_name="metadatasets_id", 
    renderer='json', 
    request_method="GET", 
    openapi=True
)
def get_metadataset(request:Request) -> MetaDataSets:
    """Create new metadataset"""
    pass
    return {}
        

@view_config(
    route_name="metadatasets_id", 
    renderer='json', 
    request_method="GET", 
    openapi=True
)
def get_metadataset(request):
    """Create new metadataset"""
    pass
    return {}
