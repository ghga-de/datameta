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

"""Testing site read capabilities via API request
"""
from . import BaseIntegrationTest
from datameta.api import base_url
from .fixtures.holders import UserFixture, FileFixture, MetaDataSetFixture
from parameterized import parameterized
import hashlib


class ReadFileAndMetadatasets(BaseIntegrationTest):

    def read_file(self, file: FileFixture, user: UserFixture, status: int = 200):
        self.testapp.get(
            f"{base_url}/files/{file.site_id}",
            headers = self.apikey_auth(user),
            status = status
        )

    def read_metadataset(self, metadataset: MetaDataSetFixture, user: UserFixture, status: int = 200):
        self.testapp.get(
            f"{base_url}/metadatasets/{metadataset.site_id}",
            headers = self.apikey_auth(user),
            status = status
        )

    def download_file_content(
        self,
        file: FileFixture,
        user: UserFixture,
        expired_download_url: bool = False,
        status_get_url: int = 307,
        status_download: int = 200
    ):
        expires = -1 if expired_download_url else 1
        response = self.testapp.get(
            base_url + f"/rpc/get-file-url/{file.site_id}?expires={expires}",
            headers = self.apikey_auth(user),
            status = status_get_url
        )

        if status_get_url == 307:
            # follow redirect:
            header_dict = {key: value for key, value in response.headerlist}
            assert "Location" in header_dict
            redirect_url = header_dict["Location"]

            # retrieve file:
            file_response = self.testapp.get(redirect_url, status = status_download)

            if not expired_download_url:
                # check if file response matched expectations:
                file_content = file_response.body
                file_checksum = hashlib.md5(file_content).hexdigest()
                assert file_checksum == file.checksum

    def setUp(self):
        super().setUp()
        self.fixture_manager.load_fixtureset('groups')
        self.fixture_manager.load_fixtureset('users')
        self.fixture_manager.load_fixtureset('apikeys')
        self.fixture_manager.load_fixtureset('services')
        self.fixture_manager.load_fixtureset('metadata')
        self.fixture_manager.load_fixtureset('files_msets')
        self.fixture_manager.load_fixtureset('submissions')
        self.fixture_manager.load_fixtureset('metadatasets')
        self.fixture_manager.copy_files_to_storage()
        self.fixture_manager.populate_metadatasets()

    @parameterized.expand(
        [
            # ("name of default file", "name of default user", expires, status_get_url, status_get_file, status_download_file)
            # owning user requests submitted file and metadataset:
            ("test_file_7", "mset_a", "user_a", False, 200, 307, 200),
            # owning user requests submitted file and metadataset and downloads with expired URL:
            ("test_file_7", "mset_a", "user_a", True, 200, 307, 404),
            # user of file-owning group requests submitted file and metadataset:
            ("test_file_7", "mset_a", "user_b", False, 200, 307, 200),
            # file-owning user requests non-submitted file:
            ("test_file_9", "mset_b", "user_b", False, 200, 307, 200),
            # user of file-owning group requests non-submitted file:
            ("test_file_9", "mset_b", "user_a", False, 403, 403, 200),
            # user not in file-owning group requests submitted and not submitted files:
            ("test_file_7", "mset_a", "user_c", False, 403, 403, 200),
            ("test_file_9", "mset_b", "user_c", False, 403, 403, 200),
            # side admin with site_read permission not in file-owning group requests submitted and not submitted files:
            ("test_file_7", "mset_a", "admin", False, 200, 307, 200),
            ("test_file_9", "mset_b", "admin", False, 403, 403, 200),
            # group admin not in file-owning group requests submitted and not submitted files:
            ("test_file_7", "mset_a", "group_y_admin", False, 403, 403, None),
            ("test_file_9", "mset_b", "group_y_admin", False, 403, 403, None),
            # site_read user not in file-owning group requests submitted and not submitted files:
            ("test_file_7", "mset_a", "user_site_read", False, 200, 307, None),
            ("test_file_9", "mset_b", "user_site_read", False, 403, 403, None),
        ]
    )
    def test_read_file_and_metadatasets(
        self,
        file_id: str,
        metadataset_id: str,
        user_id: str,
        expired_download_url: bool = False,
        status: int = 200,
        status_get_file_url: int = 307,
        status_download: int = 200

    ):
        user = self.fixture_manager.get_fixture('users', user_id)
        file = self.fixture_manager.get_fixture('files_msets', file_id)
        mset = self.fixture_manager.get_fixture('metadatasets', metadataset_id)

        self.read_file(
            file = file,
            user = user,
            status = status
        )

        self.download_file_content(
            file = file,
            user = user,
            expired_download_url = expired_download_url,
            status_get_url = status_get_file_url,
            status_download = status_download
        )

        self.read_metadataset(
            metadataset = mset,
            user = user,
            status = status
        )
