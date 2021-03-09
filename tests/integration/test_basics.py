from . import BaseIntegrationTest

class TestBasics(BaseIntegrationTest):

    def test_swagger_api_loaded(self):
        """Swagger's API Explorer should be served on /api/."""
        res = self.testapp.get("/api", status=200)
        assert "<title>Swagger UI</title>" in res.text, (
            "Swagger UI could not be loaded"
        )
