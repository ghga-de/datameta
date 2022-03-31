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

"""Testing password update via API request
"""
from parameterized import parameterized

from . import BaseIntegrationTest
from datameta.api import base_url


class TestTotpSecretDeletion(BaseIntegrationTest):

    def setUp(self):
        super().setUp()
        self.fixture_manager.load_fixtureset('groups')
        self.fixture_manager.load_fixtureset('users')
        self.fixture_manager.load_fixtureset('apikeys')

    @parameterized.expand([
        # TEST_NAME              EXEC_USER           TARGET_USER        RESP
        ("site_admin"           , "admin"            , "user_a"       , 200),
        ("group_admin"          , "group_x_admin"    , "user_a"       , 403),
        ("regular_user_self"    , "user_a"           , "user_a"       , 403),
        ("regular_user_other"   , "user_b"           , "user_a"       , 403),
        ("non_existing_user"    , "admin"            , "nihilist"     , 404),
        ])
    def test_totp_secret_deletion(self, _, executing_user: str, target_user: str, expected_response: int):

        user = self.fixture_manager.get_fixture('users', executing_user)
        target_user_before, target_user_after = None, None

        if expected_response != 404:
            target_user_before = self.fixture_manager.get_fixture_db('users', target_user)

        self.testapp.delete(
            f"{base_url}/users/{target_user}/totp-secret",
            status=expected_response,
            headers=self.apikey_auth(user)
        )

        if expected_response != 404:
            target_user_after = self.fixture_manager.get_fixture_db('users', target_user)

        if expected_response == 200:
            assert target_user_after.tfa_secret is None
        else:
            assert target_user_before is None or target_user_after.tfa_secret == target_user_before.tfa_secret
