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

"""Testing Settings via API request
"""
from parameterized import parameterized
from datameta.api import base_url
from . import BaseIntegrationTest

class TestServices(BaseIntegrationTest):
    
    def setUp(self):
        super().setUp()
        self.fixture_manager.load_fixtureset('groups')
        self.fixture_manager.load_fixtureset('users')
        self.fixture_manager.load_fixtureset('apikeys')
        self.fixture_manager.load_fixtureset('services')

    @parameterized.expand([
        # TEST_NAME                                  , EXECUTING_USER   , SERVICE_NAME                     , EXP_RESPONSE
        ("create_service_by_admin"                , "admin"             , "service_2"          , 200),
        ("create_service_by_regular_user"         , "user_a"            , "service_3"          , 403),
        ("create_service_with_existing_name"      , "admin"             , "service_0"          , 400),
    ])
    def test_create_service(self, testname: str, executing_user: str, service_name: str, expected_response: int):
        user            = self.fixture_manager.get_fixture('users', executing_user)
        auth_headers    = self.apikey_auth(user) if user else {}

        self.testapp.post_json(
            url       = f"{base_url}/services",
            params={"name": service_name},
            headers   = auth_headers,
            status    = expected_response
        )

        #Check returned info

    @parameterized.expand([
        # TEST_NAME                             , EXECUTING_USER      , SERVICE_ID  , NEW_SERVICE_NAME  , USER_LIST         , EXP_RESPONSE
        ("update_service_by_admin"              , "admin"             , "service_0"   , "service_2"       , "user_a, user_b"  , 200),
        ("update_service_by_regular_user"       , "user_a"            , "service_0"   , "service_2"       , "user_a, user_b"  , 403),
        ("update_service_to_existing_name"      , "admin"             , "service_0"   , "service_1"       , ""                , 400),
        ("update_nonexisting_service"           , "admin"             , "service_7"   , "service_1"       , ""                , 404),

    ])
    def test_update_service(self, testname: str, executing_user: str, service_id: str, new_service_name: str, user_list: str, expected_response: int):
        user            = self.fixture_manager.get_fixture('users', executing_user)
        auth_headers    = self.apikey_auth(user) if user else {}
        user_ids        = user_list.split(", ")

        self.testapp.put_json(
            url       = f"{base_url}/services/{service_id}",
            params={"name": new_service_name, "userIds": user_ids},
            headers   = auth_headers,
            status    = expected_response
        )

        #Check returned info


    @parameterized.expand([
        # TEST_NAME                           , EXECUTING_USER    , EXP_RESPONSE
        ("get_services_by_admin"              , "admin"             , 200),
        ("get_services_by_regular_user"       , "user_a"            , 403),

    ])
    def test_get_service(self, testname: str, executing_user: str, expected_response: int):
        user            = self.fixture_manager.get_fixture('users', executing_user)
        auth_headers    = self.apikey_auth(user) if user else {}

        self.testapp.get(
            url       = f"{base_url}/services",
            headers   = auth_headers,
            status    = expected_response
        )

        #Check returned info