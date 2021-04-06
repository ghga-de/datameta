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
        # TEST_NAME             EXEC_USER  TGT_USER TOKEN NEW_PW EXPIRED? RESP
        ("self_password_update", "user_a", "", "", "012345678910", False, 204),
        ("self_expired_auth", "user_a", "", "", "012345678910", True, 401),
        ("self_invalid_password", "user_a", "", "", "*meep*", False, 400),
        ("self_invalid_reset_token", "user_a", "", "this_token_does_not_exist_for_sure", "012345678910", False, 404),
        ("other_password_update", "user_a", "user_b", "", "012345678910", False, 403),
        ("other_password_update", "user_a", "nihilist", "", "012345678910", False, 403),
        ])

    def test_password_update(self, _, executing_user:str, target_user:str, token:str, new_password:str, expired_auth:bool, expected_response:int):
        if token:
            user_id = "0"
            credential = token
            auth_header = None
        else:
            user = self.users[executing_user]
            credential = user.password
            auth_header = user.expired_auth.header if expired_auth else user.auth.header
            if not target_user:
                user_id = user.site_id
            else:
                user_id = self.users[target_user].site_id if self.users.get(target_user) else target_user

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