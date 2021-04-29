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
            #("name of default file", "name of default user", expires, status_get_url, status_get_file)
            # file-owning user requests submitted file:
            ("default_file_1", "user_a", 1, 307, 200),
            # file-owning user requests submitted file and downloads with expired URL:
            ("default_file_1", "user_a", -1, 307, 404),
            # user of file-owning group requests submitted file:
            ("default_file_1", "user_b", 1, 307, 200),
            # file-owning user requests non-submitted file:
            ("default_file_5", "user_a", 1, 307, 200),
            # user of file-owning group requests non-submitted file:
            ("default_file_5", "user_b", 1, 403, None),
            # user not in file-owning group requests submitted and not submitted files:
            ("default_file_1", "user_c", 1, 403, None),
            ("default_file_5", "user_c", 1, 403, None),
            # side admin not in file-owning group requests submitted and not submitted files:
            ("default_file_1", "admin", 1, 307, 200),
            ("default_file_5", "admin", 1, 307, 200),
            # group admin not in file-owning group requests submitted and not submitted files:
            ("default_file_1", "group_y_admin", 1, 403, None),
            ("default_file_5", "group_y_admin", 1, 403, None),
        ]
    )
    def test_rpc_get_file_url(
        self,
        file_site_id:str,
        user_name:str,
        expires:int,
        status_get_url:int=307,
        status_get_file:int=200
    ):
        user = self.default_users[user_name]
        file = self.default_files[file_site_id]

        response = self.testapp.get(
            base_url + f"/rpc/get-file-url/{file.site_id}?expires={expires}",
            headers=user.auth.header,
            status=status_get_url
        )
       
        if status_get_url==307:
            # follow redirect:
            header_dict = {key: value for key, value in response.headerlist}
            assert "Location" in header_dict
            redirect_url = header_dict["Location"]

            # retrieve file:
            file_response = self.testapp.get(redirect_url, status=status_get_file)
           
            if status_get_file==200:
                # check if file response matched expectations:
                file_content = file_response.body
                file_checksum = hashlib.md5(file_content).hexdigest()
                assert file_checksum==file.checksum


