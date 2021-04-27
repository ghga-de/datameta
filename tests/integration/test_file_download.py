"""Test major download of files.
"""
from . import BaseIntegrationTest
from .fixtures import FileFixture
from typing import Optional
from parameterized import parameterized
import hashlib

from datameta.api import base_url

class TestFileDownload(BaseIntegrationTest):

    @parameterized.expand(
        [
            #("name of default file", "name of default user", status)
            # file-owning user requests submitted file:
            ("default_file_1", "user_a", 307), 
            # user of file-owning group requests submitted file:
            ("default_file_1", "user_b", 307), 
            # file-owning user requests non-submitted file:
            ("default_file_5", "user_a", 307), 
            # user of file-owning group requests non-submitted file:
            ("default_file_5", "user_b", 403), 
            # user not in file-owning group requests submitted and not submitted files:
            ("default_file_1", "user_c", 403), 
            ("default_file_5", "user_c", 403), 
            # side admin not in file-owning group requests submitted and not submitted files:
            ("default_file_1", "admin", 307), 
            ("default_file_5", "admin", 307), 
            # group admin not in file-owning group requests submitted and not submitted files:
            ("default_file_1", "group_y_admin", 403), 
            ("default_file_5", "group_y_admin", 403), 
        ]
    )
    def test_rpc_get_file_url(
        self, 
        file_site_id:str,
        user_name:str,
        status:int=307
    ):
        user = self.default_users[user_name]
        file = self.default_files[file_site_id]

        response = self.testapp.get(
            base_url + f"/rpc/get-file-url/{file.site_id}",
            headers=user.auth.header,
            status=status
        )
        
        if status==307:
            # follow redirect:
            header_dict = {key: value for key, value in response.headerlist}
            assert "Location" in header_dict
            redirect_url = header_dict["Location"]

            # retrieve file:
            file_response = self.testapp.get(redirect_url, status=200)
            
            # check if file response matched expectations:
            file_content = file_response.body
            file_checksum = hashlib.md5(file_content).hexdigest()
            assert file_checksum==file.checksum



