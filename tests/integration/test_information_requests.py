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

"""Testing user information requests via API
"""
from parameterized import parameterized

from . import BaseIntegrationTest
from datameta.api import base_url
from datameta.api.users import UserResponseElement


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
        ("normie_queries_other"               , "user_a"          , "user_c"          , 403),
        ("group_admin_own_groupmate"          , "group_x_admin"   , "user_a"          , 200),
        ("group_admin_other_group"            , "group_x_admin"   , "user_c"          , 403),
        ("site_read_query"                    , "user_site_read"  , "user_b"          , 200),
        ("site_admin_query"                   , "admin"           , "user_site_read"  , 200),
        ("site_admin_query_wrong_id"          , "admin"           , "flopsy"          , 404),
    ])
    def test_user_query(self, testname: str, executing_user: str, target_user: str, expected_response: int):
        def snake_to_camel(s):
            return ''.join(x.capitalize() if i else x for i, x in enumerate(s.split('_')))

        user = self.fixture_manager.get_fixture('users', executing_user)

        if testname == "site_admin_query_wrong_id":
            tgt_user, user_id = None, target_user
        else:
            tgt_user = self.fixture_manager.get_fixture('users', target_user)
            user_id = tgt_user.uuid

        response = self.do_request(
            user_id,
            status=expected_response,
            headers=self.apikey_auth(user),
        )

        successful_request = expected_response == 200
        privileged_request = "admin" in executing_user

        restricted_fields = map(snake_to_camel, UserResponseElement.get_restricted_fields())

        assert any((
            not successful_request,
            successful_request and all((privileged_request != (response.json.get(field) is None)) for field in restricted_fields)
        ))


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
        ("own_group"                          , "user_a"          , "group_x"         , 403),
        ("foreign_group"                      , "user_a"          , "group_y"         , 403),
        ("group_admin_own"                    , "group_x_admin"   , "group_x"         , 200),
        ("group_admin_foreign"                , "group_x_admin"   , "group_y"         , 403),
        ("site_read"                          , "user_site_read"  , "group_y"         , 200),
        ("site_admin"                         , "admin"           , "group_y"         , 200),
        ("site_admin_wrong_id"                , "admin"           , "rabbit_family"   , 404),
    ])
    def test_group_query(self, testname: str, executing_user: str, target_group: str, expected_response: int):
        user = self.fixture_manager.get_fixture('users', executing_user)

        if testname == "site_admin_wrong_id":
            tgt_group, group_id = None, target_group
        else:
            tgt_group = self.fixture_manager.get_fixture('groups', target_group)
            group_id = tgt_group.uuid

        self.do_request(
            group_id,
            status=expected_response,
            headers=self.apikey_auth(user)
        )
