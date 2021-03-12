"""Basic test that ensure that the API start correctly.
"""

from . import BaseIntegrationTest
from datameta.api import base_url

class TestBasics(BaseIntegrationTest):

    def test_swagger_api_loaded(self):
        """Swagger's API Explorer should be served on /api/."""
        res = self.testapp.get(base_url, status=200)
        assert "<title>Swagger UI</title>" in res.text, (
            "Swagger UI could not be loaded"
        )
