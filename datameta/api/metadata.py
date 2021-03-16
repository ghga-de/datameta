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
from typing import Optional, List
from pyramid.request import Request
from pyramid.view import view_config
from . import DataHolderBase
from ..models import MetaDatum
from .. import resource, security

@dataclass
class MetaDataResponseElement(DataHolderBase):
    """MetaDataSetResponse container for OpenApi communication"""
    id                      :  dict
    name                    :  str
    is_mandatory            :  bool
    order                   :  int
    is_file                 :  bool
    is_submission_unique    :  bool
    is_site_unique          :  bool
    short_description       :  Optional[str] = None
    long_description        :  Optional[str] = None
    reg_exp                 :  Optional[str] = None
    date_time_fmt           :  Optional[str] = None

@view_config(
    route_name="metadata",
    renderer='json',
    request_method="GET",
    openapi=True
)
def get(request:Request) -> List[MetaDataResponseElement]:
    """Obtain information for all metadata that are currently configured."""
    auth_user = security.revalidate_user(request)

    metadata = request.dbsession.query(MetaDatum)

    return [
            MetaDataResponseElement(
                id                    =  resource.get_identifier(metadatum),
                name                  =  metadatum.name,
                short_description     =  metadatum.short_description,
                long_description      =  metadatum.long_description,
                reg_exp               =  metadatum.regexp,
                date_time_fmt         =  metadatum.datetimefmt,
                is_mandatory          =  metadatum.mandatory,
                order                 =  metadatum.order,
                is_file               =  metadatum.isfile,
                is_submission_unique  =  metadatum.submission_unique,
                is_site_unique        =  metadatum.site_unique
                )
            for metadatum in metadata
            ]
