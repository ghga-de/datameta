from . import BaseIntegrationTest
from datameta.api import base_url

from .utils import create_file, create_metadataset


class SiteReadTest(BaseIntegrationTest):

    def test_access_staged_file(self):
        file_owner = self.users["user_a"]
        file_id = str(create_file(self.session_factory, self.storage_path.name, self.test_files[1], 1, file_owner))

        user = self.users["user_a"]

        req_args = {
            "headers": user.auth.header,
            "status": 403
        }
        
        response = self.testapp.get(
            f"{base_url}/files/{file_id}",
            **req_args
        )

    def x_test_file_deletion(self):

            user = self.users["admin"]

            file_ids = [
                str(create_file(self.session_factory, self.storage_path.name, f, i, user))
                for i, f in enumerate(self.test_files)
            ]
            
            req_args = {
                "params": {"fileIds": file_ids},
                "headers": user.auth.header,
                "status": 204
            }

            response = self.testapp.post_json(
                f"{base_url}/rpc/delete-files",
                **req_args
            )