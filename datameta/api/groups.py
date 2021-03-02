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

from pyramid.view import view_config
from pyramid.request import Request
from typing import Optional, Dict, List
from .. import models


class GroupSubmissions:
    """GroupSubmissions container for OpenApi communication"""
    submissions: List[dict]

    def __init__(self, request:Request, group_id:str):
        db = request.dbsession
        # To Developer:
        # Please insert code that queries the db
        # for all submissions for the given group_id
        # and store that list in self.submissions


    def __json__(self) -> List[dict]:
        return self(submissions)


@view_config(
    route_name="groups_id_submissions", 
    renderer='json', 
    request_method="GET", 
    openapi=True
)
def get(request: Request) -> GroupSubmissions:
    """Get all submissions of a given group."""
    pass
    return {}
    