"""Test major usage senarios related to staging and submission of
metadatasets and files.
"""

from . import BaseIntegrationTest, default_users
from .fixtures import UserFixture, AuthFixture, calc_checksum
from typing import Optional
import transaction
import os

from datameta import models
from datameta.api import base_url
from datameta.models import get_tm_session

class TestStageAndSubmitSenario(BaseIntegrationTest):
    """
    Tests ApiKey creation, metadata staging, file staging, 
    """

    def post_metadata(
        self,  
        auth:AuthFixture,
        metadata_record:dict,
        status:int=200,
    ):
        # request params:
        request_body = {
            "record": metadata_record
        }

        response = self.testapp.post_json(
            base_url + f"/metadatasets",
            headers=auth.header,
            params=request_body,
            status=status
        )

        if status==200:
            # check if response record contains same keys
            # as request record (values might have changed
            # due to backend side processing):
            assert metadata_record.keys() == response.json["record"].keys()
            
            return response.json

    
    def get_metadata(
        self,
        auth:AuthFixture,
        metadataset_id:str,
        expected_record:Optional[dict]=None,
        status:int=200
    ):
        response = self.testapp.get(
            base_url + f"/metadatasets/{metadataset_id}",
            headers=auth.header,
            status=status
        )

        if status==200:
            # check if response record contains same keys
            # as expected record (values might have changed
            # due to backend side processing):
            assert expected_record.keys() == response.json["record"].keys()

            return response.json


    def delete_metadata(
        self,
        auth:AuthFixture,
        metadataset_id:str,
        status:int=204
    ):
        response = self.testapp.delete(
            base_url + f"/metadatasets/{metadataset_id}",
            headers=auth.header,
            status=status
        )

    
    def post_file(
        self,
        auth:AuthFixture,
        name: str,
        checksum: str,
        status:int=200
    ):
        # request params:
        request_body = {
            "name": name,
            "checksum": checksum
        }

        response = self.testapp.post_json(
            base_url + f"/files",
            headers=auth.header,
            params=request_body,
            status=status
        )

        if status==200:
            return response.json


    def get_file(
        self,
        auth:AuthFixture,
        file_id:str,
        status:int=200
    ):
        response = self.testapp.get(
            base_url + f"/files/{file_id}",
            headers=auth.header,
            status=status
        )

        if status==200:
            return response.json

    
    def upload_file(
        self,
        url_to_upload:str,
        headers:str,
        file_path:str,
        file_uuid:str,
        file_checksum:str,
        status:int=204
    ):
        # with open(file_path, 'rb') as file_to_upload:
        response_upload = self.testapp.post(
            url_to_upload,
            headers=headers,
            upload_files=[("file", file_path)],
            status=status
        )

        if status == 204:
            # check if file exists in temporary storage:
            expected_file_path = os.path.join(
                self.storage_path.name,
                f"{file_uuid}__{file_checksum}"
            )
            assert os.path.exists(expected_file_path), (
                "Could not find file in storage."
            )

            # check if file has expected checksum:
            assert file_checksum == calc_checksum(expected_file_path), (
                "Checksum after upload does not meet expectation."
            )

        
    def put_file(
        self,
        auth:AuthFixture,
        file_id:str,
        name:Optional[str]=None,
        checksum:Optional[str]=None,
        content_uploaded:Optional[bool]=None,
        status:int=200
    ):
        # request params:
        request_body = {}
        if name:
            request_body["name"] = name
        if checksum:
            request_body["checksum"] = checksum
        if content_uploaded:
            request_body["contentUploaded"] = content_uploaded

        response = self.testapp.put_json(
            base_url + f"/files/{file_id}",
            headers=auth.header,
            params=request_body,
            status=status
        )

        if status==200:
            response_target_values = {
                key: val
                for key, val in response.json.items()
                if key in request_body
            }

            assert response_target_values == request_body, (
                "Requested changes did not take place."
            )
            
            return response.json

    def test_main_submission_senario(self):
        """Tests the standard usage senario for staging and 
        submitting files and metadata."""
        user = self.users["user_a"]
        
        # post metadataset:
        metadataset_ids = [
            self.post_metadata(
                auth=user.auth, 
                metadata_record=rec
            )["id"]["uuid"]
            for rec in self.metadata_records
        ]
        

        # get metadatasets and compare to original records:
        _ = [
            self.get_metadata(
                auth=user.auth, 
                metadataset_id=m_id,
                expected_record=self.metadata_records[idx]
            )
            for idx, m_id in enumerate(metadataset_ids)
        ]


        # announce files:
        file_upload_responses = [
            self.post_file(
                auth=user.auth, 
                name=file_.name, 
                checksum=file_.checksum
            )
            for file_ in self.test_files
        ]


        # check that announced files have contentUploaded set to False:
        for upload in file_upload_responses:
            file_response = self.get_file(
                auth=user.auth,
                file_id=upload["id"]["site"]
            )

            assert not file_response["contentUploaded"], (
                "The file content was set to uploaded, however, " +
                "the file has only been announced."
            )


        # upload files to provided url:
        [
            self.upload_file(
                url_to_upload=upload["urlToUpload"], 
                headers=upload["requestHeaders"], 
                file_path=self.test_files[idx].path,
                file_uuid=upload["id"]["uuid"], 
                file_checksum=self.test_files[idx].checksum,
            )
            for idx, upload in enumerate(file_upload_responses)
        ]


        # notify server that files have been uploaded:
        file_upload_responses = [
            self.put_file(
                auth=user.auth,
                file_id=upload["id"]["site"],
                content_uploaded=True
            )
            for upload in file_upload_responses
        ]


    def test_stage_and_delete_metadata(self):
        """Test whether staged metadatasets can be deleted
        after staging"""
        metadata_record = self.metadata_records[0]
        user = self.users["user_a"]

        # post metadataset:
        metadataset_id = self.post_metadata(
            auth=user.auth, 
            metadata_record=metadata_record
        )["id"]["uuid"]
        
        # delete metdataset:
        _ = self.delete_metadata(
            auth=user.auth,
            metadataset_id=metadataset_id
        )

        # expect get for deleted metadataset to fail:
        _ = self.get_metadata(
            auth=user.auth, 
            metadataset_id=metadataset_id,
            expected_record=metadata_record,
            status=404
        )
