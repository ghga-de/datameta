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

from datameta.api import base_url

from . import BaseIntegrationTest

FIXTURES_LOAD = [
    "groups",
    "users",
    "apikeys",
    "services",
    "metadata",
    "files_msets",
    "submissions",
    "metadatasets",
    "serviceexecutions",
]

# Required, with empty dict 401 is returned for a not registered user
EMPTY_AUTH_HEADER = {"Authorization": f"Bearer {None}"}


class TestGetMetricsEmptyServer(BaseIntegrationTest):
    """Test get metrics with an empty server."""

    def setUp(self):
        super().setUp()

    def test_metrics(
        self,
    ):
        response = self.testapp.get(
            url=f"{base_url}/metrics",
            status=200,
            headers=EMPTY_AUTH_HEADER,
        )

        assert response.json["metadatasetsSubmittedCount"] == 0


class TestGetMetricsServer(BaseIntegrationTest):
    """Test get metrics with data."""

    def setUp(self):
        super().setUp()
        for fixture in FIXTURES_LOAD:
            self.fixture_manager.load_fixtureset(fixture)
        self.fixture_manager.copy_files_to_storage()
        self.fixture_manager.populate_metadatasets()

    def test_metrics(
        self,
    ):
        # Get submitted metadatasets
        user = self.fixture_manager.get_fixture("users", "admin")
        auth_headers = self.apikey_auth(user) if user else {}

        response_metadatasets = self.testapp.get(
            url=f"{base_url}/metadatasets", headers=auth_headers, status=200
        )

        response_metrics = self.testapp.get(
            url=f"{base_url}/metrics",
            status=200,
            headers=EMPTY_AUTH_HEADER,
        )

        assert response_metrics.json["metadatasetsSubmittedCount"] == len(
            response_metadatasets.json
        )
