"""Testing site read capabilities via API request
"""
from . import BaseIntegrationTest
from datameta.api import base_url
from .fixtures import UserFixture, FileFixture, MetaDataSetFixture
from parameterized import parameterized
import hashlib


class ReadFileAndMetadatasets(BaseIntegrationTest):

    def read_file(self, file:FileFixture, user:UserFixture, status:int=200):
        response = self.testapp.get(
            f"{base_url}/files/{file.site_id}",
            headers=user.auth.header,
            status=status
        )


    def read_metadataset(self, metadataset:MetaDataSetFixture, user:UserFixture, status:int=200):
        response = self.testapp.get(
            f"{base_url}/metadatasets/{metadataset.site_id}",
            headers=user.auth.header,
            status=status
        )
        
    def download_file_content(
        self,
        file:FileFixture,
        user:UserFixture,
        expired_download_url:bool=False,
        status_get_url:int=307
    ):
        expires = -1 if expired_download_url else 1
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
            status_get_file = 404 if expired_download_url else 200
            file_response = self.testapp.get(redirect_url, status=status_get_file)
           
            if not expired_download_url:
                # check if file response matched expectations:
                file_content = file_response.body
                file_checksum = hashlib.md5(file_content).hexdigest()
                assert file_checksum==file.checksum



    @parameterized.expand(
        [
            #("name of default file", "name of default user", expires, status_get_url, status_get_file)
            # file-owning user requests submitted file:
            ("default_file_1", "metadataset_01", "user_a", False, 200, 307),
            # file-owning user requests submitted file and downloads with expired URL:
            ("default_file_1", "metadataset_01", "user_a", True, 200, 307),
            # user of file-owning group requests submitted file:
            ("default_file_1", "metadataset_01", "user_b", False, 200, 307),
            # file-owning user requests non-submitted file:
            ("default_file_5", "metadataset_03", "user_a", False, 200, 307),
            # user of file-owning group requests non-submitted file:
            ("default_file_5", "metadataset_03", "user_b", False, 403, 403),
            # user not in file-owning group requests submitted and not submitted files:
            ("default_file_1", "metadataset_01", "user_c", False, 403, 403),
            ("default_file_5", "metadataset_03", "user_c", False, 403, 403),
            # side admin not in file-owning group requests submitted and not submitted files:
            ("default_file_1", "metadataset_01", "admin", False, 200, 307),
            ("default_file_5", "metadataset_03", "admin", False, 403, 403),
            # group admin not in file-owning group requests submitted and not submitted files:
            ("default_file_1", "metadataset_01", "group_y_admin", False, 403, 403),
            ("default_file_5", "metadataset_03", "group_y_admin", False, 403, 403),
            # site_read user not in file-owning group requests submitted and not submitted files:
            ("default_file_1", "metadataset_01", "group_z_site_read", False, 200, 307),
            ("default_file_5", "metadataset_03", "group_z_site_read", False, 403, 403),
        ]
    )
    def test_read_file_and_metadatasets(
        self, 
        file_id:str, 
        metadataset_id:str, 
        user_id:str, 
        expired_download_url:bool=False,
        status:int=200,
        status_get_file_url:int=307

    ):
        user = self.default_users[user_id]
        file = self.default_files[file_id]
        metadataset = self.default_metadatasets[metadataset_id]
        
        # self.read_file(
        #     file=file,
        #     user=user,
        #     status=status
        # )

        self.download_file_content(
            file=file,
            user=user,
            expired_download_url=expired_download_url,
            status_get_url=status_get_file_url
        )

        # self.read_metadataset(
        #     metadataset=metadataset,
        #     user=user,
        #     status=status
        # )