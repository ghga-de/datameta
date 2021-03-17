# Copyright (c) 2021 Universität Tübingen, Germany
# Authors: Leon Kuchenbecker <leon.kuchenbecker@uni-tuebingen.de>,
#          Moritz Hahn <moritz.hahn@uni-tuebingen.de>
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
from pyramid.httpexceptions import HTTPNoContent, HTTPForbidden, HTTPNotFound

from dataclasses import dataclass
from . import DataHolderBase
from ..models import User, Group
from .. import security, errors
from ..resource import resource_by_id

# @dataclass
# class SiteRequestResponse(DataHolderBase):
#     """Class for Site Request Response from OpenApi"""
#     settings: List[dict]

# @view_config(
#     route_name="site", 
#     renderer='json', 
#     request_method="GET", 
#     openapi=True
# )
# def get(request: Request) -> SiteRequestResponse:
#     """Return all Site Settings"""

#     #settings = new List[dict]

#     db = request.dbsession

#     # Authenticate the user
#     auth_user = security.revalidate_user(request)

#     # User has to be site admin to access these settings
#     if not auth_user.site_admin:
#         raise HTTPForbidden()

    
#     #return SiteRequestResponse(
#     #    settings: settings
#     #)
