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

no_service_metadata   = {'ZIP Code', 'ID', 'FileR1', 'Date', 'FileR2'}
all_metadata          = no_service_metadata.union({ 'ServiceMeta0' , 'ServiceMeta1' })

class TestGetMetaDataSets(BaseIntegrationTest):

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
        # Unauthenticated users should get a 401
        ("unauthenticated", None, "submittedBefore=123", [], [], False, 401),
        # A reqular user queries all metadatasets but has access to none
        ("unauthorized", 'user_c', "", [], [], False, 404),
        # A regular user sending a query with no results (submittedAfter far in the future)
        ("regular_no_result", "user_a", "submittedAfter=2100-05-20T16:51:48.622354%2B00:00", [], [], False, 404),
        # A regular user querying all records with a permissive submittedBefore. Sees all metadatasets but the unsubmitted mset_b.
        ("regular_user_all", "user_a", "submittedBefore=2100-05-20T16:51:48.622354%2B00:00", {'mset_a', 'mset_a_sexec', 'mset_b_sexec'}, no_service_metadata, False, 200),
        # A regular user attempts to query metadata that are awaiting service execution but isn't allowed to query service executions
        ("regular_user_service", "user_a", "awaitingService=service_0", None, None, False, 400),
        # A service user queries metadatasets that are awaiting service execution and retrieves the only submitted sample without service execution
        ("service_user_service", "service_user_0", "awaitingService=service_0", {'mset_a'}, all_metadata, True, 200),
        # A service user queries part of the metadatasets by specifying a submission time boundary that applies to a subset of metadatasets
        ("service_user_before", "service_user_0", "submittedBefore=2021-01-02T00:00:00%2B00:00", {'mset_a', 'mset_a_sexec'}, all_metadata, True, 200),
        # A service user queries part of the metadatasets by specifying a submission time boundary that applies to a subset of metadatasets
        ("service_user_after", "service_user_0", "submittedAfter=2021-01-02T00:00:00%2B00:00", {'mset_b_sexec'}, all_metadata, True, 200),
        # A service user queries part of the metadatasets by specifying a submission time boundary and an awaitingService constraint
        ("service_user_combined", "service_user_0", "awaitingService=service_0&submittedBefore=2021-01-02T00:00:00%2B00:00", {'mset_a'}, all_metadata, True, 200),
        ])
    def test_query_metadatasets(self, _,
            executing_user:str,
            query_string:str,
            expected_mset_ids:list,
            expected_metadata:list,
            expected_with_service_executions:bool,
            expected_status:int):

        user = self.fixture_manager.get_fixture('users', executing_user) if executing_user else None
        auth_headers = self.apikey_auth(user) if user else {}

        response = self.testapp.get(
            url       = f"{base_url}/metadatasets?{query_string}",
            headers   = auth_headers,
            status    = expected_status
        )

        if expected_status== 200:
            # Check if the returned metadatasets are the expected ones
            returned_mset_ids = { mset['id']['site'] for mset in response.json }
            assert returned_mset_ids == expected_mset_ids, "Returned metadatasets did not match expected ones"

            # Check if the returned metadata are the expected ones. That is,
            # for users who cannot read the service metadata, those should not
            # be part of the 'record' attribute of each metadataset.
            returned_metadata = { key for mset in response.json for key in mset['record'] }
            assert returned_metadata == expected_metadata, "Returned metadata did not match expected metadata"

            # Check whether the service executions are present or absent
            if expected_with_service_executions:
                assert all(isinstance(mset['serviceExecutions'], dict) for mset in response.json)
            else:
                assert all(mset['serviceExecutions'] is None for mset in response.json)
