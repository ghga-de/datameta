"""Testing bulk deletion via API request
"""
from parameterized import parameterized

from . import BaseIntegrationTest
from datameta.api import base_url

from .utils import create_file, create_metadataset

class BulkDeletionTest(BaseIntegrationTest):

    def test_file_deletion(self):
        user = self.default_users["user_a"]

        file_ids = [
            site_id 
            for site_id, file in self.default_files.items() 
            if not file.submitted
        ]

        response = self.testapp.post_json(
            f"{base_url}/rpc/delete-files",
            params={"fileIds": file_ids},
            headers=user.auth.header,
            status=204
        )

    def test_mds_deletion(self):
        user = self.default_users["user_a"]
        
        metadataset_ids = [
            site_id
            for site_id, mset in self.default_metadatasets.items()
            if not mset.submitted
        ]

        response = self.testapp.post_json(
            f"{base_url}/rpc/delete-metadatasets",
            params={"metadatasetIds": metadataset_ids},
            headers=user.auth.header,
            status=204
        )