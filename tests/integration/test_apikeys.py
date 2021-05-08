"""Test to check APIKey-related endpoint.
"""

from . import BaseIntegrationTest
from .utils import get_auth_header
from typing import Optional

from datameta.api import base_url

class TestApiKeyUsageSenario(BaseIntegrationTest):
    """
    Tests ApiKey creation, usage, and deletion.
    """

    def post_key(
        self, 
        email:str,
        password:str,
        label:str="test_key",
        status:int=200, 
    ):
        """Request ApiKey"""
        request_body = {
            "email": email,
            "password": password,
            "label": label
        }

        response = self.testapp.post_json(
            base_url + "/keys",
            params=request_body,
            status=status
        )

        if status==200:
            return response.json


    def get_all_keys(
        self, 
        user_id: str,
        token: str,
        expected_key_id:Optional[dict] = None,
        status:int=200
    ):
        """Get a list of all ApiKeys"""
        response = self.testapp.get(
            base_url + f"/users/{user_id}/keys",
            headers=get_auth_header(token),
            status=status
        )

        if status==200:
            # check if prev token is in list of tokens:
            if expected_key_id:
                curr_ids = [key["id"]["uuid"] for key in response.json]
                assert expected_key_id in curr_ids, (
                    "List of APIKeys does not contain the previously created one."
                )

            return response.json


    def delete_key(
        self,
        apikey_id:str,
        token:str,
        status:int=200
    ):
        """Delete ApiKey"""
        response = self.testapp.delete(
            base_url + f"/keys/{apikey_id}",
            headers=get_auth_header(token),
            status=status
        )

    def setUp(self):
        super().setUp()
        self.fixture_manager.load_fixtureset('groups')
        self.fixture_manager.load_fixtureset('users')

    def test_create_get_delete_apikey(self):
        # set initial state:
        user = self.fixture_manager.get_fixture('users', 'user_a')

        # create apikey:
        user_session = self.post_key(user.email, user.password)
        token = user_session["token"]
        token_id = user_session["id"]["uuid"]

        # use apikey to authenticate for getting all apikeys
        # and check if previously created key is contained:
        _ = self.get_all_keys(
            user_id=user.site_id,
            token=token,
            expected_key_id=token_id
        )

        # delete apikey:
        self.delete_key(apikey_id=token_id, token=token)

        # run one more step to confirm that
        # after deleting the ApiKey
        # using it for authenication fails:
        _ = self.get_all_keys(
            user_id=user.site_id,
            token=token,
            expected_key_id=token_id,
            status=401
        )
