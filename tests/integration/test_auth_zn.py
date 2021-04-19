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

import transaction
import datetime

from parameterized import parameterized_class
from datameta.models import get_tm_session, ApiKey, User
from datameta.api import base_url
from datameta import security

from . import BaseIntegrationTest, utils

def setUpNoAuth(self):
    """
    Set up authentication for the test scenario "no authentication"
    """
    self.auth_headers = {}

def setUpCookieAuth(self):
    """
    Set up authentication for the test scenario "cookie authentication"
    """
    self.auth_headers = {}

    # Perform login
    response = self.testapp.post(
            "/login",
            status = 302,
            params = {
                'input_email' : self.users['user_a'].email,
                'input_password' : self.users['user_a'].password
                }
            )

    # Set received cookie
    cookie, value = response.headers['Set-Cookie'].split(";")[0].split("=")
    self.testapp.set_cookie(cookie.strip(), value.strip())

def setUpToken(self, expired):
    """
    Set up authentication for the test scenario "bearer authentication"

    Args:
        expired - if true, the configured token will be set to expire in the past
    """
    with transaction.manager:
        if expired:
            self.auth_headers = self.users['user_a'].expired_auth.header
        else:
            self.auth_headers = self.users['user_a'].auth.header

@parameterized_class([
    { "auth" : None              , "expect_authn" : False  , "setup_func" : setUpNoAuth},
    { "auth" : "cookie"          , "expect_authn" : True   , "setup_func" : setUpCookieAuth },
    { "auth" : "bearer"          , "expect_authn" : True   , "setup_func" : lambda session_factory : setUpToken(session_factory, False)},
    { "auth" : "bearer_expired"  , "expect_authn" : False  , "setup_func" : lambda session_factory : setUpToken(session_factory, True)},
    ],
    class_name_func = lambda _x, _y, params : "authn_" + str(params["auth"])
    )
class TestAuthzAndAuthn(BaseIntegrationTest):

    def setUp(self):
        # Run the super class setup which creates users
        super().setUp()

        # Perform test-specific setup
        self.setup_func()

    def test_get_keys_own(self):
        """GET /users/{ownid}/keys"""
        response = self.testapp.get(
                base_url + "/users/user_a/keys",
                headers = self.auth_headers,
                status = 200 if self.expect_authn else 401
                )

    def test_get_keys_foreign(self):
        """GET /users/{foreignid}/keys"""
        response = self.testapp.get(
                base_url + "/users/user_b/keys",
                headers = self.auth_headers,
                status = 403 if self.expect_authn else 401
                )

    def test_get_metadata(self):
        """GET /metadata"""
        response = self.testapp.get(
                base_url + "/metadata",
                headers = self.auth_headers,
                status = 200 if self.expect_authn else 401
                )

    def test_post_submissions(self):
        """POST /submissions"""
        response = self.testapp.post_json(
                base_url + "/submissions",
                headers = self.auth_headers,
                # Invalid if authn
                status = 400 if self.expect_authn else 401,
                params = {
                    "metadatasetIds": [],
                    "fileIds": [],
                    "label": "string"
                    }
                )

    def test_post_validation(self):
        """POST /presubvalidation"""
        response = self.testapp.post_json(
                base_url + "/presubvalidation",
                headers = self.auth_headers,
                # Invalid if authn
                status = 400 if self.expect_authn else 401,
                params = {
                    "metadatasetIds": [],
                    "fileIds": [],
                    "label": "string"
                    }
                )

    def test_get_appsettings(self):
        """GET /appsettings"""
        response = self.testapp.get(
                base_url + "/appsettings",
                headers = self.auth_headers,
                # Requires admin, must return 403 for non-admin
                status = 403 if self.expect_authn else 401
                )

