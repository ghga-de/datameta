"""Test major usage senarios related to staging and submission of
metadatasets and files.
"""

from . import BaseIntegrationTest, default_users
from .fixtures import UserFixture, AuthFixture, calc_checksum
from typing import Optional, List, Any, Dict
import transaction
import os

from datameta import models
from datameta.api import base_url
from datameta.models import get_tm_session

class TestStageAndSubmitSenario(BaseIntegrationTest):
    """
    Tests ApiKey creation, metadata staging, file staging, 
    """

    def _file_exists_in_storage(
        self, 
        file_uuid:str, 
        file_checksum:str,
        compare_checksum:bool=True
    ):
        expected_file_path = os.path.join(
            self.storage_path.name,
            f"{file_uuid}__{file_checksum}"
        )

        return os.path.exists(expected_file_path)

        if file_exists and compare_checksum:
            return file_checksum == calc_checksum(expected_file_path)

        return file_exists


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
            assert expected_record is not None and expected_record.keys() == response.json["record"].keys()

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
        response = self.testapp.post(
            url_to_upload,
            headers=headers,
            upload_files=[("file", file_path)],
            status=status
        )

        if status == 204:
            # check if file exists in temporary storage:
            assert self._file_exists_in_storage(
                file_uuid=file_uuid, 
                file_checksum=file_checksum
            ), (
                "Could not find file in storage or " +
                "checksum after upload did not meet the expectations."
            )


    def delete_file(
        self,
        auth:AuthFixture,
        file_id:str,
        file_uuid:Optional[str]=None,
        file_checksum:Optional[str]=None,
        status:int=204
    ):
        response = self.testapp.delete(
            base_url + f"/files/{file_id}",
            headers=auth.header,
            status=status
        )

        if status == 204 and file_uuid and file_checksum:
            # check that file does not exist in storage anymore:
            assert not self._file_exists_in_storage(
                file_uuid=file_uuid, 
                file_checksum=file_checksum,
                compare_checksum=False
            ), (
                "File is still present in storage."
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
        request_body : Dict[str, Any] = {}
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


    def post_presubvalidation(
        self,
        auth:AuthFixture,
        metadataset_ids: List[str],
        file_ids: List[str],
        label:str="test_submission",
        status:int=204
    ):
        # request params:
        request_body = {
            "metadatasetIds": metadataset_ids,
            "fileIds": file_ids,
            "label": label
        }

        response = self.testapp.post_json(
            base_url + f"/presubvalidation",
            headers=auth.header,
            params=request_body,
            status=status
        )


    def post_submission(
        self,
        auth:AuthFixture,
        metadataset_ids: List[str],
        file_ids: List[str],
        label:str="test_submission",
        status:int=200
    ):
        # request params:
        request_body = {
            "metadatasetIds": metadataset_ids,
            "fileIds": file_ids,
            "label": label
        }

        response = self.testapp.post_json(
            base_url + f"/submissions",
            headers=auth.header,
            params=request_body,
            status=status
        )

        if status==200:
            return response.json


    def get_all_submissions(
        self,
        auth:AuthFixture,
        group_id:str,
        expected_submission_uuid:Optional[str]=None,
        status:int=200
    ):
        # with open(file_path, 'rb') as file_to_upload:
        response = self.testapp.get(
            base_url + f"/groups/{group_id}/submissions",
            headers=auth.header,
            status=status
        )

        if status == 200:
            if expected_submission_uuid:
                submission_uuids = [
                    sub["id"]["uuid"]
                    for sub in response.json
                ]
                assert expected_submission_uuid in submission_uuids, (
                    "Expected submission was not contained in response."
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
            )["id"]["site"]
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
        _ = [
            self.put_file(
                auth=user.auth,
                file_id=upload["id"]["site"],
                content_uploaded=True
            )
            for upload in file_upload_responses
        ]
        
        # check if pre-submission validation passes:
        file_ids = [file_["id"]["site"] for file_ in file_upload_responses]
        self.post_presubvalidation(
            auth=user.auth, 
            metadataset_ids=metadataset_ids, 
            file_ids=file_ids
        )

        # post submission:
        submission_response = self.post_submission(
            auth=user.auth, 
            metadataset_ids=metadataset_ids, 
            file_ids=file_ids
        )

        # get all submission and check if posted submission
        # is contained in the response:
        self.get_all_submissions(
            auth=user.auth,
            group_id=user.group_site_id,
            expected_submission_uuid=submission_response["id"]["uuid"]
        )

        # check if files and metadatasets can still be accessed
        # after submission:
        _ = [
            self.get_metadata(
                auth=user.auth, 
                metadataset_id=m_id,
                expected_record=self.metadata_records[idx]
            )
            for idx, m_id in enumerate(metadataset_ids)
        ]
        
        _ = [
            self.get_file(
                auth=user.auth,
                file_id=upload["id"]["site"]
            )
            for upload in file_upload_responses
        ]

        # try to delete/modify submitted files and metadata,
        # expect all of that to fail:
        for metadataset_id in metadataset_ids:
            self.delete_metadata(
                auth=user.auth, 
                metadataset_id=metadataset_id,
                status=403
            )

        for idx, upload in enumerate(file_upload_responses):
            file_id = upload["id"]["site"]
            self.delete_file(
                auth=user.auth, 
                file_id=file_id,
                status=403
            )

            self.put_file(
                auth=user.auth, 
                file_id=file_id,
                status=403
            )

            try:
                self.upload_file(
                    url_to_upload=upload["urlToUpload"], 
                    headers=upload["requestHeaders"], 
                    file_path=self.test_files[idx].path,
                    file_uuid=file_id, 
                    file_checksum=self.test_files[idx].checksum,
                )
                raise AssertionError(
                    "Upload succeeded after submitting the file."
                )
            except:
                pass
            

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


    def test_announce_and_delete_file(self):
        """Test whether staged metadatasets can be deleted
        after staging"""
        test_file = self.test_files[0]
        user = self.users["user_a"]

        # announce file:
        file_upload_response = self.post_file(
            auth=user.auth, 
            name=test_file.name, 
            checksum=test_file.checksum
        )

        # upload file to provided url:
        _ = self.upload_file(
            url_to_upload=file_upload_response["urlToUpload"], 
            headers=file_upload_response["requestHeaders"], 
            file_path=test_file.path,
            file_uuid=file_upload_response["id"]["uuid"], 
            file_checksum=test_file.checksum,
        )

        # delete file:
        _ = self.delete_file(
            auth=user.auth,
            file_id=file_upload_response["id"]["site"],
            file_uuid=file_upload_response["id"]["uuid"],
            file_checksum=test_file.checksum
        )

        # confirm that file info cannot be obtained anymore:
        _ = self.get_file(
            auth=user.auth,
            file_id=file_upload_response["id"]["site"],
            status=404
        )

        # confirm that upload to original URL fails:
        try:
            _ = self.upload_file(
                url_to_upload=file_upload_response["urlToUpload"], 
                headers=file_upload_response["requestHeaders"], 
                file_path=test_file.path,
                file_uuid=file_upload_response["id"]["uuid"], 
                file_checksum=test_file.checksum
            )
            raise AssertionError(
                "Upload succeeded after deleting the file."
            )
        except:
            pass
