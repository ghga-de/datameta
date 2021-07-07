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

from parameterized import parameterized

from datameta.api import base_url

from . import BaseIntegrationTest


class MsetReplacementTest(BaseIntegrationTest):
    def setUp(self):
        super().setUp()
        self.fixture_manager.load_fixtureset('groups')
        self.fixture_manager.load_fixtureset('users')
        self.fixture_manager.load_fixtureset('apikeys')
        self.fixture_manager.load_fixtureset('services')
        self.fixture_manager.load_fixtureset('metadata')
        self.fixture_manager.load_fixtureset('files_msets')
        self.fixture_manager.load_fixtureset('files_independent')
        self.fixture_manager.load_fixtureset('submissions')
        self.fixture_manager.load_fixtureset('metadatasets')
        self.fixture_manager.load_fixtureset('serviceexecutions')
        self.fixture_manager.copy_files_to_storage()
        self.fixture_manager.populate_metadatasets()

    @parameterized.expand([
        ("success", "group_x_admin", 200),
    ])
    def test_mset_replacement(self, testname: str, executing_user: str, expected_status: int):
        user = self.fixture_manager.get_fixture("users", executing_user) if executing_user else None
        auth_headers = self.apikey_auth(user) if user else {}

        request_body = {
            "record": {
                "Date": "2021-07-01",
                "ZIP Code": "108",
                "ID": "XC13",  # this is weird: when using the swagger interface, you can use the key "#ID", is that # stripped off somewhere?
                "FileR2": "group_x_file_1.txt",
                "FileR1": "group_x_file_2.txt"
            },
            "replaces": [
                "mset_a"
            ],
            "replacesLabel": "because i can",
            "fileIds": [
                "group_x_file_1", "group_x_file_2"
            ]
        }

        self.testapp.post_json(
            url       = f"{base_url}/rpc/replace-metadatasets",
            headers   = auth_headers,
            status    = expected_status,
            params    = request_body
        )
