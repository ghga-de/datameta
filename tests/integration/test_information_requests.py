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

"""Testing user management via API request
"""
from parameterized import parameterized

from . import BaseIntegrationTest
from datameta.api import base_url


class TestUserInformationRequest(BaseIntegrationTest):

    def setUp(self):
        super().setUp()
        self.fixture_manager.load_fixtureset('groups')
        self.fixture_manager.load_fixtureset('users')
        self.fixture_manager.load_fixtureset('apikeys')

    def do_request(self, user_uuid, **params):
        response = self.testapp.get(
            f"{base_url}/users/{user_uuid}",
            **params
        )
        return response

    @parameterized.expand([
        # TEST_NAME                           , EXECUTING USER    , TARGET_USER       , EXP_RESPONSE
        ("self_query"                         , "user_a"          , "user_a"          , 200),
        ("normie_queries_other"               , "user_a"          , "user_c"          , 404),
        ("group_admin_own_groupmate"          , "group_x_admin"   , "user_a"          , 200),
        ("group_admin_other_group"            , "group_x_admin"   , "user_c"          , 404),
        ("site_read_query"                    , "user_site_read"  , "user_b"          , 200),
        ("site_admin_query"                   , "admin"           , "user_site_read"  , 200),
    ])
    def test_user_query(self, testname: str, executing_user: str, target_user: str, expected_response: int):
        user          = self.fixture_manager.get_fixture('users', executing_user)
        tgt_user      = self.fixture_manager.get_fixture('users', target_user)

        self.do_request(
            tgt_user.uuid,
            status=expected_response,
            headers=self.apikey_auth(user),
        )


class TestGroupInformationRequest(BaseIntegrationTest):

    def setUp(self):
        super().setUp()
        self.fixture_manager.load_fixtureset('groups')
        self.fixture_manager.load_fixtureset('users')
        self.fixture_manager.load_fixtureset('apikeys')

    def do_request(self, group_uuid, **params):
        response = self.testapp.get(
            f"{base_url}/groups/{group_uuid}",
            **params
        )
        return response

    @parameterized.expand([
        # TEST_NAME                           , EXECUTING USER    , TARGET_GROUP      , EXP_RESPONSE
        ("own_group"                          , "user_a"          , "group_x"         , 200),
        ("foreign_group"                      , "user_a"          , "group_y"         , 404),
        ("group_admin_own"                    , "group_x_admin"   , "group_x"         , 200),
        ("group_admin_foreign"                , "group_x_admin"   , "group_y"         , 404),
        ("site_read"                          , "user_site_read"  , "group_y"         , 200),
        ("site_admin"                         , "admin"           , "group_y"         , 200),
    ])
    def test_group_query(self, testname: str, executing_user: str, target_group: str, expected_response: int):
        user          = self.fixture_manager.get_fixture('users', executing_user)
        tgt_group     = self.fixture_manager.get_fixture('groups', target_group)

        self.do_request(
            tgt_group.uuid,
            status=expected_response,
            headers=self.apikey_auth(user)
        )
