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

"""Testing tracking of failed login attempts
"""
from parameterized import parameterized

from . import BaseIntegrationTest
from datameta.api import base_url
from .utils import get_auth_header


class TestLoginTracking(BaseIntegrationTest):

    def setUp(self):
        super().setUp()
        self.fixture_manager.load_fixtureset('groups')
        self.fixture_manager.load_fixtureset('users')
        self.fixture_manager.load_fixtureset('apikeys')

    @parameterized.expand([
        # TEST_NAME                    EXEC_USER   SUCCESS?  EXPECTED_OUTCOME
        ("login_failure_with_block"  , "user_a"  , False   , (302, "login", False)),
        ("login_success_after_n-1"   , "user_a"  , True    , (302, "home", True)),
    ])
    def test_login_tracking_via_login(self, _, executing_user: str, success: bool, expected_outcome):

        user = self.fixture_manager.get_fixture('users', executing_user)
        n_attempts = 5
        self.set_application_setting("security_max_failed_login_attempts", n_attempts)

        for attempt in range(1, n_attempts + 1):
            form = self.testapp.get("/login").forms[0]
            form["input_email"] = user.email
            form["input_password"] = user.password + ("_somenonsense" if attempt < n_attempts or not success else "")
            response = form.submit("form.submitted")

        form = self.testapp.get("/login").forms[0]
        form["input_email"] = user.email
        form["input_password"] = user.password
        response = form.submit("form.submitted")

        db_user = self.fixture_manager.get_fixture_db("users", executing_user)

        assert (response.status_int, response.location.split("/")[-1], db_user.enabled) == expected_outcome

    @parameterized.expand([
        # TEST_NAME                    EXEC_USER   SUCCESS?  EXPECTED_OUTCOME
        ("login_failure_with_block"  , "user_a"  , False   , (401, False)),
        ("login_success_after_n-1"   , "user_a"  , True    , (200, True)),
    ])
    def test_login_tracking_via_apikey(self, _, executing_user: str, success: bool, expected_outcome):

        n_attempts = 5
        self.set_application_setting("security_max_failed_login_attempts", n_attempts)

        for attempt in range(1, n_attempts + 1):
            failed_attempt = attempt < n_attempts or not success
            apikey = self.fixture_manager.get_fixture('apikeys', executing_user + ("_expired" if failed_attempt else ""))

            self.testapp.get(
                f"{base_url}/rpc/whoami",
                headers=get_auth_header(apikey.value_plain),
                status=401 if failed_attempt else 200
            )

        apikey = self.fixture_manager.get_fixture('apikeys', executing_user)
        response = self.testapp.get(
            f"{base_url}/rpc/whoami",
            status=expected_outcome[0],
            headers=get_auth_header(apikey.value_plain)
        )

        db_user = self.fixture_manager.get_fixture_db("users", executing_user)

        assert (response.status_int, db_user.enabled) == expected_outcome
