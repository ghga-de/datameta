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

from pyramid.request import Request
from pyramid.view import view_config

from ..models import MetaDataSet, Submission
from . import DataHolderBase

log = logging.getLogger(__name__)


@dataclass
class MetricsBase(DataHolderBase):
    """Base class for Metrics communication to OpenApi"""

    pass


@dataclass
class MetricsResponse(MetricsBase):
    """MetricsResponse container for OpenApi communication"""

    metadatasets_submitted_count: int


@view_config(
    route_name="metrics",
    renderer="json",
    request_method="GET",
    openapi=True,
)
def metrics(request: Request) -> MetricsResponse:
    """Get metrics of the server."""
    db = request.dbsession

    query = db.query(MetaDataSet).filter(MetaDataSet.submission_id.isnot(None))

    metadatasets_submitted_count = int(query.count())

    log.info("Server metrics requested.")

    return MetricsResponse(
        metadatasets_submitted_count=metadatasets_submitted_count,
    )
