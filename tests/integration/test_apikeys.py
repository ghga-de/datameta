"""Test to check APIKey-related endpoint.
"""

from . import BaseIntegrationTest, default_users
from .utils import get_auth_headers

from datameta import models
from datameta.api import base_url

class TestApiKeyUsageSenario(BaseIntegrationTest):
    """
    Tests ApiKey creation, usage, and deletion.
    """

    def step_1(self, status:int=200):
        """Request ApiKey"""
        request_body = {
            "email": self.state["user"].email,
            "password": self.state["user"].password,
            "label": self.state["apikey_label"]
        }
        
        response = self.testapp.post_json(
            base_url + "/keys", 
            params=request_body, 
            status=status
        ) 
        
        if status==200:
            self.state["apikey_response"] = response.json

    def step_2(self, status:int=200):
        """Get a list of all ApiKeys"""
        # request params:
        user_id = self.state["user"].uuid
        token = self.state["apikey_response"]["token"] # previously created apikey 
        request_headers = get_auth_headers(token)

        response = self.testapp.get(
            base_url + f"/users/{user_id}/keys",
            headers=request_headers,
            status=status
        ) 

        if status==200:
            # check whether current response is consistent with the previous responce
            # obtained when creating the api keys
            keys_to_compare = ["apikeyId", "label", "expiresAt"]
            curr_response = {
                key: value 
                for key, value in response.json[0].items()
                if key in keys_to_compare
            }
            prev_response = {
                key: value 
                for key, value in self.state["apikey_response"].items()
                if key in keys_to_compare
            }
            assert curr_response == prev_response, (
                "List of ApiKeys didn't contain the previously created apikey."
            )

    def step_3(self, status=200):
        """Delete ApiKey"""
        apikey_id = self.state["apikey_response"]["apikeyId"] # previously created apikey 
        token = self.state["apikey_response"]["token"] # previously created apikey 
        request_headers = get_auth_headers(token)

        response = self.testapp.delete(
            base_url + f"/keys/{apikey_id}",
            headers=request_headers,
            status=status
        ) 

    def test_steps(self):
        # set initial state:
        self.state = {
            "user": self.users["user_a"],
            "apikey_label": "test_key",
            "apikey_response": None # slot to store the apikey response
        }

        # execute all test steps:
        # - create apikey
        # - use it to fetch all tokens of that user
        # - delete the apikey
        self._test_all_steps()

        # run one more step to confirm that
        # after deleting the ApiKey
        # using it for authenication fails:
        self.step_2(status=401)
