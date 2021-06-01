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

from sqlalchemy.orm import joinedload

from datameta.api import base_url
from datameta import models

from . import BaseIntegrationTest

class ServiceExecutionTest(BaseIntegrationTest):
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
        self.fixture_manager.load_fixtureset('serviceexecutions')
        self.fixture_manager.copy_files_to_storage()
        self.fixture_manager.populate_metadatasets()

        
    
    @parameterized.expand([
        ("unauthorized_no_user", "",  "313", "x", 401),
        ("forbidden_no_service_user", "admin", "service_0", "mset_a", 403),
        ("forbidden_service_already_executed", "service_user_0", "service_0", "mset_a_sexec", 403),
        ("success", "service_user_0", "service_0", "mset_a", 200),
        ("missing_file_mdatum", "service_user_0", "service_0", "mset_a", 400),
        ("file_mdatum_set_to_nonfile", "service_user_0", "service_0", "mset_a", 400),
        ("unreferenced_file", "service_user_0", "service_0", "mset_a", 400),
    ])
    def test_service_execution(self, testname: str, executing_user: str, service_id: str, mset_id: str, expected_status: int):
        user = self.fixture_manager.get_fixture('users', executing_user) if executing_user else None
        auth_headers = self.apikey_auth(user) if user else {}

        test_data = {
            "success": {
                "record": {"ServiceMeta0": 313, "ServiceMeta1": "test_file_unreferenced.txt"},
                "fileIds": ["test_file_unreferenced"]
            },
            "missing_file_mdatum": {
                "record": {"ServiceMeta0": 313},
                "fileIds": []
            },
            "file_mdatum_set_to_nonfile": {
                "record": {"ServiceMeta1": 313},
                "fileIds": []
            },
            "unreferenced_file": {
                "record": {"ServiceMeta0": 313, "ServiceMeta1": "test_file_service_0"},
                "fileIds": ["test_file_service_0", "test_file_unreferenced"]
            }
        }

        request_body = test_data.get(testname, test_data["success"])

        response = self.testapp.post_json(
            url       = f"{base_url}/service-execution/{service_id}/{mset_id}",
            headers   = auth_headers,
            status    = expected_status,
            params    = request_body
        )

        if expected_status == 200:
          mset_after = self.fixture_manager.get_fixture_db("metadatasets", mset_id, joinedload(models.MetaDataSet.service_executions).joinedload(models.ServiceExecution.service))
          assert service_id in (sexec.service.site_id for sexec in mset_after.service_executions), f"Service {service_id} was not executed."

          mset_after = self.fixture_manager.get_fixture_db("metadatasets", mset_id, joinedload(models.MetaDataSet.metadatumrecords).joinedload(models.MetaDatumRecord.metadatum))
          mdrecords = {mdr.metadatum.name: mdr.value for mdr in mset_after.metadatumrecords}
          for key, value in request_body.get("record", dict()).items():
              assert mdrecords.get(key) == str(value), f"Metadata was not set as expected {key}: {mdrecords.get(key)}, expected: {value}"