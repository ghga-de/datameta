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

from datameta.security.tfaz import get_user_2fa_secret, generate_otp


class TestLoginTracking(BaseIntegrationTest):

    def setUp(self):
        super().setUp()
        self.fixture_manager.load_fixtureset('groups')
        self.fixture_manager.load_fixtureset('users')
        self.fixture_manager.load_fixtureset('apikeys')

    @parameterized.expand([
        # TEST_NAME                    EXEC_USER   SUCCESS?  EXPECTED_OUTCOME
        ("login_failure_with_block"  , "user_a"  , False   , (302, False)),
        ("login_success_after_n-1"   , "user_a"  , True    , (302, True)),
    ])
    def test_login_tracking_via_login_no_2fa(self, _, executing_user: str, success: bool, expected_outcome):

        if self.settings["datameta.tfa.enabled"]:
            expected_location = "tfa" if success else "login"
        else:
            expected_location = "home" if success else "login"

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

        assert (response.status_int, db_user.enabled) == expected_outcome and response.location.split("/")[-1] == expected_location

    @parameterized.expand([
        # TEST_NAME                    EXEC_USER   SUCCESS?  EXPECTED_OUTCOME
        ("login_failure_with_block"  , "user_a"  , False   , (302, False)),
        ("login_success_after_n-1"   , "user_a"  , True    , (302, True)),
    ])
    def test_login_tracking_via_login_and_2fa(self, _, executing_user: str, success: bool, expected_outcome):

        if not self.settings["datameta.tfa.enabled"]:
            assert True

        else:

            user = self.fixture_manager.get_fixture('users', executing_user)
            n_attempts = 5
            self.set_application_setting("security_max_failed_login_attempts", n_attempts)

            form = self.testapp.get("/login").forms[0]
            form["input_email"] = user.email
            form["input_password"] = user.password
            response = form.submit("form.submitted")

            location = response.location.split("/")[-1]
            assert location == "tfa"

            db_user = self.fixture_manager.get_fixture_db("users", executing_user)
            secret = get_user_2fa_secret(db_user, settings=self.settings)

            for attempt in range(1, n_attempts + 1):
                form = self.testapp.get("/tfa").forms[0]
                otp = str(generate_otp(secret))
                if attempt < n_attempts or not success:
                    otp = "111111" if otp != "111111" else "999999"
                form["input_otp"] = str(otp)
                response = form.submit("form.submitted")

            expected_location = "home" if success else "login"
            db_user = self.fixture_manager.get_fixture_db("users", executing_user)

            assert response.location.split("/")[-1] == expected_location and (response.status_int, db_user.enabled) == expected_outcome

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
