"""Testing bulk deletion via API request
"""
from parameterized import parameterized

from . import BaseIntegrationTest
from datameta.api import base_url

from .utils import create_file, create_metadataset

class BulkDeletionTest(BaseIntegrationTest):

    def test_file_deletion(self):
        user = self.users["user_a"]

        response = self.testapp.post_json(
            f"{base_url}/rpc/delete-files",
            params={"fileIds": list(self.default_files.keys())},
            headers=user.auth.header,
            status=204
        )

    def test_mds_deletion(self):
        user = self.users["user_a"]

        response = self.testapp.post_json(
            f"{base_url}/rpc/delete-metadatasets",
            params={"metadatasetIds": list(self.default_metadatasets.keys())},
            headers=user.auth.header,
            status=204
        )