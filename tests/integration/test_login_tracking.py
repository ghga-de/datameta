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

from datameta.models import User
from datameta.settings import get_setting


class TestLoginTracking(BaseIntegrationTest):

    def setUp(self):
        super().setUp()
        self.fixture_manager.load_fixtureset('groups')
        self.fixture_manager.load_fixtureset('users')

    @parameterized.expand([
        # TEST_NAME                 EXEC_USER SUCCESS?  EXPECTED_OUTCOME
        ("login_fail_with_block"  , "user_a", False   , (302, "login", False)),
        ("login_success_after_n-1", "user_a", True    , (302, "home", True)),
    ])
    def test_login_tracking(self, _, executing_user: str, success: bool, expected_outcome):

        user = self.fixture_manager.get_fixture('users', executing_user)
        n_attempts = get_setting(self.fixture_manager.get_db(), "security_max_failed_login_attempts")

        for attempt in range(1, n_attempts + 1):

            form = self.testapp.get("/login").forms[0]
            form["input_email"] = user.email
            form["input_password"] = user.password + ("_somenonsense" if attempt < n_attempts or not success else "")
            response = form.submit("form.submitted")

        form = self.testapp.get("/login").forms[0]
        form["input_email"] = user.email
        form["input_password"] = user.password
        response = form.submit("form.submitted")

        user_db = self.fixture_manager.get_db().query(User).filter(User.email == user.email).one_or_none()

        assert (response.status_int, response.location.split("/")[-1], user_db.enabled) == expected_outcome
