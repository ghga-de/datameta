from . import BaseIntegrationTest

class TestAuthSenario(BaseIntegrationTest):

    def test_swagger_api_loaded(self):
        """Swagger's API Explorer should be served on /api/."""
        res = self.testapp.get("/api", status=200)
        assert "<title>Swagger UI</title>" in res.text, (
            "Swagger UI could not be loaded"
        )

    # def test_apikey_request(self):
        # apikey = self.testapp.post("/api/keys", status=200)
