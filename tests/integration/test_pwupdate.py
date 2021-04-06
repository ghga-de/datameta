"""Testing password update via API request
"""
import time
from datetime import datetime, timedelta

from parameterized import parameterized

from . import BaseIntegrationTest
from datameta.api import base_url
from .utils import create_pwtoken

class TestPasswordUpdate(BaseIntegrationTest):

    @parameterized.expand([
        # TEST_NAME             EXEC_USER TOKEN NEW_PW RESP
        ("self_password_update", "user_a", "", "012345678910", 204),
        ("self_invalid_password_update", "user_a", "", "*meep*", 400),
        ("self_invalid_reset_token", "user_a", "this_token_does_not_exist_for_sure", "012345678910", 404),
        ])

    def test_password_update(self, _, executing_user:str, token:str, new_password:str, expected_response:int):
        if token:
            user_id = "0"
            credential = token
            auth_header = None
        else:
            user = self.users[executing_user]
            user_id = user.site_id
            credential = user.password
            auth_header = user.auth.header

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

        response = self.testapp.put_json(
            f"{base_url}/users/{user_id}/password",
            **req_json
        )

    def test_failure_own_password_update_expired_apitoken(self, status:int=401):
        """Testing unsuccessful (self-)password change with expired api token.

        Expected Response:
            HTTP 401
        """
        user = self.users["user_a"]

        request_body = {
            "passwordChangeCredential": user.password,
            "newPassword": "012345678910"
        }

        response = self.testapp.put_json(
            f"{base_url}/users/{user.site_id}/password",
            headers=user.expired_auth.header,
            params=request_body,
            status=status
        )

    def test_failure_other_password_update(self, status:int=403):
        """Testing unsuccessful password change for other user.

        Expected Response:
            HTTP 403
        """
        attacker, victim = self.users["user_a"], self.users["user_b"]

        request_body = {
            "passwordChangeCredential": attacker.password,
            "newPassword": "012345678910"
        }

        response = self.testapp.put_json(
            f"{base_url}/users/{victim.site_id}/password",
            headers = attacker.auth.header,
            params = request_body,
            status=status
        )

    def test_failure_invalid_user_password_update(self, status:int=403):
        """Testing unsuccessful (self-)password change for invalid/non-existing user

        Expected Response:
            HTTP 403
        """
        attacker = self.users["user_a"]

        request_body = {
            "passwordChangeCredential": attacker.password,
            "newPassword": "012345678910"
        }

        response = self.testapp.put_json(
            f"{base_url}/users/nihilist/password",
            headers = attacker.auth.header,
            params = request_body,
            status=status
        )

    def test_failure_expired_reset_token(self, status:int=410):
        """Testing unsuccessful (self-)password change with expired token.

        Expected Response:
            HTTP 410
        """
        user = self.users["user_a"]
        pwtoken = create_pwtoken(self.session_factory, user, expires=datetime.now() + timedelta(minutes=-1))

        request_body = {
            "passwordChangeCredential": pwtoken,
            "newPassword": "012345678910"
        }

        response = self.testapp.put_json(
            f"{base_url}/users/0/password",
            headers = user.auth.header,
            params = request_body,
            status = status
        )

    def test_successful_own_password_reset(self, status:int=204):
        """Testing successful (self-)password change via reset token.
        Expected Response:
            HTTP 204
        """
        user = self.users["user_b"]
        pwtoken = create_pwtoken(self.session_factory, user)

        request_body = {
            "passwordChangeCredential": pwtoken,
            "newPassword": "012345678910"
        }

        response = self.testapp.put_json(
            base_url + f"/users/0/password",
            headers=user.auth.header,
            params=request_body,
            status=status
        )