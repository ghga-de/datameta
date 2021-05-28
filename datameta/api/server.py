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

from pyramid.view import view_config
from pyramid.request import Request

from dataclasses import dataclass
from . import DataHolderBase, api_version

import datameta


@dataclass
class ServerInfoResponse(DataHolderBase):
    api_version: str
    datameta_version: str


@view_config(
    route_name="server",
    renderer='json',
    request_method="GET",
    openapi=True
)
def get(request: Request) -> ServerInfoResponse:
    return ServerInfoResponse(
            api_version        = api_version,
            datameta_version   = datameta.__version__
    )
