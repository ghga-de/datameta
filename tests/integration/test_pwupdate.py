"""Testing password update via API request
"""
import time
from datetime import datetime, timedelta

from . import BaseIntegrationTest
from datameta.api import base_url
from .utils import create_pwtoken


class TestPasswordUpdate(BaseIntegrationTest):

    def test_successful_own_password_update(self, status:int=204):
        """Testing successful (self-)password change.

        Expected Response:
            HTTP 204
        """
        user = self.users["user_a"]

        request_body = {
            "passwordChangeCredential": user.password,
            "newPassword": "012345678910"
        }

        response = self.testapp.put_json(
            base_url + f"/users/{user.site_id}/password",
            headers=user.auth.header,
            params=request_body,
            status=status
        )

    def test_failure_invalid_password_update(self, status:int=400):
        """Testing unsuccessful (self-)password change with invalid password.

        Expected Response:
            HTTP 400
        """
        user = self.users["user_a"]

        request_body = {
            "passwordChangeCredential": user.password,
            "newPassword": "*meep*"
        }

        response = self.testapp.put_json(
            base_url + f"/users/{user.site_id}/password",
            headers=user.auth.header,
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
            base_url + f"/users/{victim.site_id}/password",
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
            base_url + f"/users/nihilist/password",
            headers = attacker.auth.header,
            params = request_body,
            status=status
        )

    def test_failure_invalid_reset_token(self, status:int=404):
        """Testing unsuccessful (self-)password change with invalid token.

        Expected Response:
            HTTP 404
        """
        user = self.users["user_a"]

        request_body = {
            "passwordChangeCredential": "this_token_does_not_exist_for_sure",
            "newPassword": "012345678910"
        }

        response = self.testapp.put_json(
            base_url + f"/users/0/password",
            headers = user.auth.header,
            params = request_body,
            status = status
        )

    def test_failure_expired_reset_token(self, status:int=410):
        """Testing unsuccessful (self-)password change with expired token.

        Expected Response:
            HTTP 410
        """
        user = self.users["user_a"]
        pwtoken = create_pwtoken(self.session_factory, user, expires=datetime.now() + timedelta(seconds=1))
        time.sleep(5)

        request_body = {
            "passwordChangeCredential": pwtoken,
            "newPassword": "012345678910"
        }

        response = self.testapp.put_json(
            base_url + f"/users/0/password",
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
            base_url + f"/users/{user.site_id}/password",
            headers=user.expired_auth.header,
            params=request_body,
            status=status
        )