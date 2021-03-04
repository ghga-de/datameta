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
from typing import Optional, Dict, List
from .. import models


# For Developers: if needed change the dataclasses to
# regular classes and supply custom __init__ functions
# (for instance if create of that class object should
# also trigger creation of the respective db model)

@dataclass
class SubmissionBase:
    """Base class for Submission communication to OpenApi"""
    metadataset_ids: List[str]
    file_ids: List[str]

    def _json(self) -> dict:
        return {
                "metaDataSetIds": self.metadataset_ids,
                "fileIds": self.file_ids
            }


@dataclass
class SubmissionRequest(SubmissionBase):
    """SubmissionRequest container for OpenApi communication"""

    def __json__(self, request: Request) -> dict:
        
        return self._json()


@dataclass
class SubmissionResponse(SubmissionBase):
    """SubmissionResponse container for OpenApi communication"""
    submission_id:str

    def __json__(self, request: Request) -> dict:
        json_ = self._json()
        json_.update(        
            {
                "submissionId": self.submission_id
            }
        )
        return json_


@view_config(
    route_name="submissions", 
    renderer='json', 
    request_method="POST", 
    openapi=True
)
def post(request: Request) -> SubmissionResponse:
    """Create a Submission."""
    pass
    return {}
