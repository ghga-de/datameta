"""Testing bulk deletion via API request
"""
from . import BaseIntegrationTest
from datameta.api import base_url

class BulkDeletionTest(BaseIntegrationTest):

    def setUp(self):
        super().setUp()
        self.fixture_manager.load_fixtureset('groups')
        self.fixture_manager.load_fixtureset('users')
        self.fixture_manager.load_fixtureset('apikeys')

    def test_file_deletion(self):
        self.fixture_manager.load_fixtureset('files_independent')
        self.fixture_manager.copy_files_to_storage()

        user           = self.fixture_manager.get_fixture('users', 'user_a')
        auth_headers   = self.apikey_auth(user)
        files          = self.fixture_manager.get_fixtureset('files_independent')

        file_ids = [ file.site_id for file in files.values() ]

        response = self.testapp.post_json(
            f"{base_url}/rpc/delete-files",
            params={"fileIds": file_ids},
            headers=auth_headers,
            status=204
        )

    def test_mds_deletion(self):
        self.fixture_manager.load_fixtureset('metadatasets_a_unsubmitted')

        user           = self.fixture_manager.get_fixture('users', 'user_a')
        msets          = self.fixture_manager.get_fixtureset('metadatasets_a_unsubmitted')
        auth_headers   = self.apikey_auth(user)

        metadataset_ids = [ mset.site_id for mset in msets.values() ]

        response = self.testapp.post_json(
            f"{base_url}/rpc/delete-metadatasets",
            params={"metadatasetIds": metadataset_ids},
            headers=auth_headers,
            status=204
        )
