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

from . import BaseIntegrationTest
from typing import List, Dict

from datameta.api import base_url


class TestMetaDatumUniqueNotMandatory(BaseIntegrationTest):
    """Test behavior of MetaDatum with unique and not mandatory flag set"""

    def post_metadata(
        self,
        headers: Dict,
        metadata_record: Dict,
        status: int = 200,
    ):
        # request params:
        request_body = {
            "record": metadata_record
        }

        response = self.testapp.post_json(
            base_url + "/metadatasets",
            headers = headers,
            params = request_body,
            status = status
        )

        if status == 200:
            # check if response record contains same keys
            # as request record (values might have changed
            # due to backend side processing):
            assert metadata_record.keys() == response.json["record"].keys()

            return response.json

    def post_presubvalidation(
        self,
        headers: dict,
        metadataset_ids: List[str],
        file_ids: List[str],
        label: str = "test_submission",
        status: int = 204
    ):
        # request params:
        request_body = {
            "metadatasetIds": metadataset_ids,
            "fileIds": file_ids,
            "label": label
        }

        self.testapp.post_json(
            base_url + "/presubvalidation",
            headers = headers,
            params = request_body,
            status = status
        )

    def post_submission(
        self,
        headers: Dict,
        metadataset_ids: List[str],
        file_ids: List[str],
        label: str = "test_submission",
        status: int = 200
    ):
        # request params:
        request_body = {
            "metadatasetIds": metadataset_ids,
            "fileIds": file_ids,
            "label": label
        }

        response = self.testapp.post_json(
            base_url + "/submissions",
            headers = headers,
            params = request_body,
            status = status
        )

        if status == 200:
            return response.json

    def setUp(self):
        super().setUp()
        self.fixture_manager.load_fixtureset('groups')
        self.fixture_manager.load_fixtureset('users')
        self.fixture_manager.load_fixtureset('apikeys')
        self.fixture_manager.load_fixtureset('metadatum_unique_not_mandatory')
        self.fixture_manager.load_fixtureset('metadatasets_unique_not_mandatory', database_insert = False)
        self.fixture_manager.populate_metadatasets()

        self.metadatasets = [ mset for _, mset in self.fixture_manager.get_fixtureset('metadatasets_unique_not_mandatory').items() ]
        self.metadataset_records = [ { k: v for k, v in mset.records.items() } for mset in self.metadatasets ]

    def test_metadatum_unique_not_mandatory_submission(self):
        """Try to submit MetaDataSet with unique not mandatory MetaDatum"""

        user               = self.fixture_manager.get_fixture('users', 'user_a')
        auth_headers       = self.apikey_auth(user)

        # post metadataset
        metadataset_ids = [
            self.post_metadata(
                headers = auth_headers,
                metadata_record = record
            )["id"]["site"]
            for record in self.metadataset_records
        ]

        # presubvalidation
        file_ids = []
        self.post_presubvalidation(
            headers = auth_headers,
            metadataset_ids = metadataset_ids,
            file_ids = []
        )

        # post submission
        self.post_submission(
            headers = auth_headers,
            metadataset_ids = metadataset_ids,
            file_ids = file_ids
        )
