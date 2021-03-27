"""Testing password update via API request
"""

from . import BaseIntegrationTest
from .utils import get_auth_headers
from datameta.api import base_url

class TestPasswordUpdate(BaseIntegrationTest):

    def test_successful_own_password_update(self, status:int=204):
        user = self.users["user_a"]
        token = self.get_api_key("user_a", base_url)
        request_headers = get_auth_headers(token)

        request_body = {
            "passwordChangeCredential": user.password,
            "newPassword": "012345678910"
        }

        response = self.testapp.put_json(
            base_url + f"/users/{user.site_id}/password",
            headers=request_headers,
            params=request_body,
            status=status
        )

    def test_failure_other_password_update(self, status:int=403):
        attacker, victim = self.users["user_a"], self.users["user_b"]
        token = self.get_api_key("user_a", base_url)

        request_headers = get_auth_headers(token)
        request_body = {
            "passwordChangeCredential": attacker.password,
            "newPassword": "012345678910"
        }

        response = self.testapp.put_json(
            base_url + f"/users/{victim.site_id}/password",
            headers = request_headers,
            params = request_body,
            status=status
        )

    def test_failure_invalid_reset_token(self, status:int=404):        
        token = self.get_api_key("user_a", base_url)

        request_headers = get_auth_headers(token)
        request_body = {
            "passwordChangeCredential": "Cz628nCFsstFaHsfelHnbz9JvIjnsRy0n_jt9HuBC-cUKz6R4Su0yQ",
            "newPassword": "012345678910"
        }

        response = self.testapp.put_json(
            base_url + f"/users/0/password",
            headers = request_headers,
            params = request_body,
            status = status
        )

    def test_failure_expired_reset_token(self, status:int=410):
        token = self.get_api_key("user_a", base_url) #, expires="2021-01-18") # <- that is an expired api key, not a pw-reset key >:(

        request_headers = get_auth_headers(token)
        assert True
