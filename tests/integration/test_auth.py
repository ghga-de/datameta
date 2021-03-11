from . import BaseIntegrationTest, default_users
from datameta import models

class TestApiKeyUsageSenario(BaseIntegrationTest):
    """
    Tests ApiKey creation, usage, and deletion.
    """

    def step_1_req_apikey(self):
        """Request ApiKey"""
        request_body = {
            "email": self.state["user"].email,
            "password": self.state["user"].password,
            "label": self.state["apikey_label"]
        }
        
        response = self.testapp.post_json(
            "/api/keys", 
            params=request_body, 
            status=200
        ) 
        
        self.state["apikey_response"] = response.json

    def step_2_list_apikeys(self):
        """Get a list of all ApiKeys"""
        # request params:
        user_id = self.state["user"].uuid
        token = self.state["apikey_response"]["token"] # previously created apikey 
        request_headers = {
            "Authorization": f"Bearer {token}"
        }

        response = self.testapp.get(
            f"/api/users/{user_id}/keys",
            headers=request_headers,
            status=200
        ) 

        # check whether current response is consistent with the previous responce
        # obtained when creating the api keys
        keys_to_compare = ["apiKeyId", "label", "expiresAt"]
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

    def test_steps(self):
        # set initial state:
        self.state = {
            "user": self.users["user"],
            "apikey_label": "test_key",
            "apikey_response": None # slot to store the apikey response
        }

        # execute all test steps
        self._test_all_steps()
