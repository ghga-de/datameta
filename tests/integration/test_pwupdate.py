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

from .utils import get_auth_header
from . import BaseIntegrationTest
from datameta.api import base_url
from .fixtures import FixtureNotFoundError


class TestPasswordUpdate(BaseIntegrationTest):

    def setUp(self):
        super().setUp()
        self.fixture_manager.load_fixtureset('groups')
        self.fixture_manager.load_fixtureset('users')
        self.fixture_manager.load_fixtureset('apikeys')
        self.fixture_manager.load_fixtureset('passwordtokens')
        self.fixture_manager.load_fixtureset('usedpasswords')

    @parameterized.expand([
        # TEST_NAME                           EXEC_USER    TGT_USER_ID    TOKEN_FIXTURE            NEW_PW                EXPIRED  RESP
        ("self_pw_update_oldpass"           , "user_a"   , None         , None                   , "Xy.012345678910"   , False   , 204),
        ("self_pw_update_reset_token"       , "user_a"   , None         , "user_a_reset_token"   , "Xy.012345678910"   , False   , 204),
        ("self_pw_update_reset_exp_token"   , "user_a"   , None         , "user_a_reset_token"   , "Xy.012345678910"   , True    , 410),
        ("self_expired_auth"                , "user_a"   , None         , None                   , "Xy.012345678910"   , True    , 401),
        ("self_invalid_password"            , "user_a"   , None         , None                   , "*meep*"            , False   , 400),
        ("self_invalid_reset_token"         , "user_a"   , None         , "does_not_exist"       , "Xy.012345678910"   , False   , 404),
        ("other_password_update"            , "user_a"   , "user_b"     , None                   , "Xy.012345678910"   , False   , 403),
        ("other_password_update"            , "user_a"   , "nihilist"   , None                   , "Xy.012345678910"   , False   , 403),
        ("self_pw_update_reuse_pw"          , "user_d"   , None         , None                   , "Xy.012345678910"   , False   , 400),
        ])
    def test_password_update(self, _, executing_user: str, target_user_id: str, token_fixture: str, new_password: str, expired_auth: bool, expected_response: int):
        if token_fixture:
            user_id = "0"
            try:
                token = self.fixture_manager.get_fixture('passwordtokens', token_fixture + ("_expired" if expired_auth else ""))
                credential = token.value_plain
            except FixtureNotFoundError:
                credential = "invalid_token"
            auth_header = None
        else:
            user = self.fixture_manager.get_fixture('users', executing_user)
            credential = user.password
            apikey = self.fixture_manager.get_fixture('apikeys', executing_user + ("_expired" if expired_auth else ""))
            auth_header = get_auth_header(apikey.value_plain)
            if not target_user_id:
                user_id = user.site_id
            else:
                user_id = target_user_id

        request_body = {
            "passwordChangeCredential": credential,
            "newPassword": new_password
        }

        req_json = {
            "params": request_body,
            "status": expected_response
        }

        if auth_header:
            req_json["headers"] = auth_header

        self.testapp.put_json(
            f"{base_url}/users/{user_id}/password",
            **req_json
        )
