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
from parameterized import parameterized
from datameta.api import base_url
import os
import hashlib


def calc_checksum(file_path: str) -> str:
    """Calculate the checksum of a file"""
    with open(file_path, "rb") as file_:
        byte_content = file_.read()
        return hashlib.md5(byte_content).hexdigest()


class TestSubmittedMetaDataSetDelete(BaseIntegrationTest):

    def setUp(self):
        super().setUp()
        self.fixture_manager.load_fixtureset('groups')
        self.fixture_manager.load_fixtureset('users')
        self.fixture_manager.load_fixtureset('apikeys')
        self.fixture_manager.load_fixtureset('services')
        self.fixture_manager.load_fixtureset('metadata')
        self.fixture_manager.load_fixtureset('files_msets')
        self.fixture_manager.load_fixtureset('files_metadatasets_submitted_delete')
        self.fixture_manager.load_fixtureset('submissions')
        self.fixture_manager.load_fixtureset('metadatasets')
        self.fixture_manager.load_fixtureset('metadatasets_submitted_delete')
        self.fixture_manager.load_fixtureset('serviceexecutions')
        self.fixture_manager.copy_files_to_storage(exclude=['test_file_not_exists'])
        self.fixture_manager.populate_metadatasets()

    def file_exists_in_storage(
        self,
        file_uuid: str,
        file_checksum: str,
        compare_checksum: bool = True
    ) -> bool:
        """Check if a file exists in the storage and optionally compare the checksums"""
        expected_file_path = os.path.join(
            self.storage_path,
            f"{file_uuid}__{file_checksum}"
        )

        file_exists = os.path.exists(expected_file_path)

        if file_exists and compare_checksum:
            return file_checksum == calc_checksum(expected_file_path)

        return file_exists

    @parameterized.expand([
        ('Success', 'admin', 'mset_a' , 200),
        ('Success', 'admin', 'mset_no_files', 200),
        ('Success', 'admin', 'mset_a_sexec', 200),
        ('Success', 'admin', 'mset_b_sexec', 200),
        ('Not submitted', 'admin', 'mset_b', 403),
        ('File not exists', 'admin', 'mset_file_not_exists', 500),
        ('Unauthorized', 'user_a', 'mset_a', 401),
        ('Unauthorized', 'group_x_admin', 'mset_a', 401),
        ('Unauthorized', 'user_site_read', 'mset_a', 401),
        ])
    def test_delete_submitted_metadatasets(self,
            _: str,
            executing_user: str,
            metadataset_id: str,
            expected_status: int,
            ):

        user = self.fixture_manager.get_fixture('users', executing_user) if executing_user else None
        auth_headers = self.apikey_auth(user) if user else {}

        # Admin header for GET requests
        user_admin = self.fixture_manager.get_fixture('users', 'admin')
        auth_headers_admin = self.apikey_auth(user_admin) if user else {}

        response = self.testapp.get(
            url       = f"{base_url}/metadatasets",
            headers   = auth_headers_admin,
            status    = 200
        )
        returned_metadataset_ids = { mset['id']['site'] for mset in response.json }

        # If metadataset was submitted it should be in the list
        if expected_status == 403:
            assert metadataset_id not in returned_metadataset_ids, f"Metadataset {metadataset_id} was found"
        else:
            assert metadataset_id in returned_metadataset_ids, f"Metadataset {metadataset_id} was not found"

        response_delete = self.testapp.delete(
            url       = f"{base_url}/metadatasets/submitted/{metadataset_id}",
            headers   = auth_headers,
            status    = expected_status
        )

        # If deletion was successful, check if metadataset and files were deleted
        if response_delete.status == "success":
            response = self.testapp.get(
                url       = f"{base_url}/metadatasets",
                headers   = auth_headers_admin,
                status    = 200
            )
            returned_mset_ids = { mset['id']['site'] for mset in response.json }
            assert metadataset_id not in returned_mset_ids, f"Metadataset {metadataset_id} was found"

            # Check if files are deleted
            if response_delete.json["fileIds"]:
                for file in response_delete.json["fileIds"]:
                    fixture_file = self.fixture_manager.get_fixture('files_msets', file["site"])
                    assert not self.file_exists_in_storage(file["uuid"], fixture_file.checksum), f"File {file['site']} was not deleted"

        if response_delete.status == 500:
            response = self.testapp.get(
                url       = f"{base_url}/metadatasets",
                headers   = auth_headers_admin,
                status    = 200
            )
            returned_mset_ids = { mset['id']['site'] for mset in response.json }
            assert metadataset_id in returned_mset_ids, f"Metadataset {metadataset_id} was not found"
