"""Testing bulk deletion via API request
"""
from parameterized import parameterized

from . import BaseIntegrationTest
from datameta.api import base_url

from .utils import create_file, create_metadataset

class BulkDeletionTest(BaseIntegrationTest):

    def test_file_deletion(self):

        user = self.users["admin"]

        file_ids = [
            str(create_file(self.session_factory, f, i, user))
            for i, f in enumerate(self.test_files)
        ]
        
        req_json = {
            "params": {"fileIds": file_ids},
            "headers": user.auth.header,
            "status": 204
        }

        response = self.testapp.post_json(
            f"{base_url}/rpc/delete-files",
            **req_json
        )

    def test_mds_deletion(self):
        user = self.users["admin"]

        mds_ids = [
            str(create_metadataset(self.session_factory, i, user))
            for i, _ in enumerate(self.metadata_records)
        ]

        req_json = {
            "params": {"metadatasetIds": mds_ids},
            "headers": user.auth.header,
            "status": 204
        }