from . import BaseIntegrationTest

class TestApiKeyUsageSenario(BaseIntegrationTest):
    """
    Tests ApiKey creation, usage, and deletion.
    """

    def step_1_req_apikey(self):
        """Request ApiKey"""
        request_body = {
            "email": "admin@admin.admin",
            "password": "admin",
            "label": "test"
        }
        response_body = self.testapp.post_json("/api/keys", request_body, status=200) 
        assert False, str(request_body)

    def test_steps(self):
        self._test_all_steps()
