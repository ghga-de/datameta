# Copyright 2021 Universität Tübingen, DKFZ and EMBL for the German Human Genome-Phenome Archive (GHGA)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Test major usage senarios related to staging and submission of
metadatasets and files.
"""

from . import BaseIntegrationTest
from .utils import get_file_path
from typing import Optional, List, Any, Dict
import os
import hashlib

from datameta.api import base_url

def calc_checksum(file_path:str):
    with open(file_path, "rb") as file_:
        byte_content = file_.read()
        return hashlib.md5(byte_content).hexdigest()

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
            self.storage_path,
            f"{file_uuid}__{file_checksum}"
        )

        file_exists = os.path.exists(expected_file_path)

        if file_exists and compare_checksum:
            return file_checksum == calc_checksum(expected_file_path)

        return file_exists

    def post_metadata(
        self,
        headers:dict,
        metadata_record:dict,
        status:int=200,
    ):
        # request params:
        request_body = {
            "record": metadata_record
        }

        response = self.testapp.post_json(
            base_url + f"/metadatasets",
            headers=headers,
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
        headers:dict,
        metadataset_id:str,
        expected_record:Optional[dict]=None,
        status:int=200
    ):
        response = self.testapp.get(
            base_url + f"/metadatasets/{metadataset_id}",
            headers=headers,
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
        headers:dict,
        metadataset_id:str,
        status:int=204
    ):
        response = self.testapp.delete(
            base_url + f"/metadatasets/{metadataset_id}",
            headers=headers,
            status=status
        )


    def post_file( self,
        headers: dict,
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
            headers=headers,
            params=request_body,
            status=status
        )

        if status==200:
            return response.json


    def get_file(
        self,
        headers:dict,
        file_id:str,
        status:int=200
    ):
        response = self.testapp.get(
            base_url + f"/files/{file_id}",
            headers=headers,
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
        headers:dict,
        file_id:str,
        file_uuid:Optional[str]=None,
        file_checksum:Optional[str]=None,
        status:int=204
    ):
        response = self.testapp.delete(
            base_url + f"/files/{file_id}",
            headers=headers,
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
        headers:dict,
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
            headers=headers,
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
        headers:dict,
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
            headers=headers,
            params=request_body,
            status=status
        )


    def post_submission(
        self,
        headers:dict,
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
            headers=headers,
            params=request_body,
            status=status
        )

        if status==200:
            return response.json


    def get_all_submissions(
        self,
        headers:dict,
        group_id:str,
        expected_submission_uuid:Optional[str]=None,
        status:int=200
    ):
        # with open(file_path, 'rb') as file_to_upload:
        response = self.testapp.get(
            base_url + f"/groups/{group_id}/submissions",
            headers=headers,
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



    def setUp(self):
        super().setUp()
        self.fixture_manager.load_fixtureset('groups')
        self.fixture_manager.load_fixtureset('users')
        self.fixture_manager.load_fixtureset('apikeys')
        self.fixture_manager.load_fixtureset('services')
        self.fixture_manager.load_fixtureset('metadata')
        self.fixture_manager.load_fixtureset('metadatasets', database_insert=False)
        self.fixture_manager.populate_metadatasets()

        self.metadatasets                      = [ mset for name, mset in self.fixture_manager.get_fixtureset('metadatasets').items() if name in ['mset_a', 'mset_b'] ]
        self.non_service_metadata              = { mdat.name for mdat in self.fixture_manager.get_fixtureset('metadata').values() if mdat.service is None }
        self.non_service_metadataset_records   = [ { k:v for k,v in mset.records.items() if k in self.non_service_metadata } for mset in self.metadatasets ]

    def test_main_submission_senario(self):
        """Tests the standard usage senario for staging and
        submitting files and metadata."""
        # Load the 'files_msets' fixtures without database insert, i.e. without staging
        self.fixture_manager.load_fixtureset('files_msets', database_insert=False)

        user               = self.fixture_manager.get_fixture('users', 'user_a')
        group              = self.fixture_manager.get_fixture(**user.group)
        auth_headers       = self.apikey_auth(user)
        files              = self.fixture_manager.get_fixtureset('files_msets')
        files              = [ file_fixture for name, file_fixture in files.items() if name in ['test_file_7', 'test_file_8', 'test_file_9', 'test_file_10']]


        # post metadataset:
        metadataset_ids = [
            self.post_metadata(
                headers=auth_headers,
                metadata_record=record
            )["id"]["site"]
            for record in self.non_service_metadataset_records
        ]

        # get metadatasets and compare to original records:
        _ = [
            self.get_metadata(
                headers=auth_headers,
                metadataset_id=m_id,
                expected_record=record
            )
            for m_id, record in zip(metadataset_ids, self.non_service_metadataset_records)
        ]

        # announce files:
        file_upload_responses = [
                self.post_file(
                    headers = auth_headers,
                    name=file.name,
                    checksum=file.checksum
                    )
                for file in  files
                ]

        # check that announced files have contentUploaded set to False:
        for upload in file_upload_responses:
            file_response = self.get_file(
                headers=auth_headers,
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
                file_path=get_file_path(files[idx].name),
                file_uuid=upload["id"]["uuid"],
                file_checksum=files[idx].checksum,
            )
            for idx, upload in enumerate(file_upload_responses)
        ]

        # notify server that files have been uploaded:
        _ = [
            self.put_file(
                headers=auth_headers,
                file_id=upload["id"]["site"],
                content_uploaded=True
            )
            for upload in file_upload_responses
        ]

        # check if pre-submission validation passes:
        file_ids = [file_["id"]["site"] for file_ in file_upload_responses]
        self.post_presubvalidation(
            headers=auth_headers,
            metadataset_ids=metadataset_ids,
            file_ids=file_ids
        )

        # post submission:
        submission_response = self.post_submission(
            headers=auth_headers,
            metadataset_ids=metadataset_ids,
            file_ids=file_ids
        )

        # get all submission and check if posted submission
        # is contained in the response:
        self.get_all_submissions(
            headers=auth_headers,
            group_id=group.site_id,
            expected_submission_uuid=submission_response["id"]["uuid"]
        )

        # check if files and metadatasets can still be accessed
        # after submission:
        _ = [
            self.get_metadata(
                headers=auth_headers,
                metadataset_id=m_id,
                expected_record=record
            )
            for m_id, record in zip(metadataset_ids, self.non_service_metadataset_records)
        ]

        _ = [
            self.get_file(
                headers=auth_headers,
                file_id=upload["id"]["site"]
            )
            for upload in file_upload_responses
        ]

        # try to delete/modify submitted files and metadata,
        # expect all of that to fail:
        for metadataset_id in metadataset_ids:
            self.delete_metadata(
                headers=auth_headers,
                metadataset_id=metadataset_id,
                status=403
            )

        for idx, upload in enumerate(file_upload_responses):
            file_id = upload["id"]["site"]
            self.delete_file(
                headers=auth_headers,
                file_id=file_id,
                status=403
            )

            self.put_file(
                headers=auth_headers,
                file_id=file_id,
                status=403
            )

            self.upload_file(
                url_to_upload=upload["urlToUpload"],
                headers=upload["requestHeaders"],
                file_path=get_file_path(files[idx].name),
                file_uuid=file_id,
                file_checksum=files[idx].checksum,
                status=409 # This must fail as the file was already uploaded
            )

    def test_stage_and_delete_metadata(self):
        """Test whether staged metadatasets can be deleted
        after staging"""
        user              = self.fixture_manager.get_fixture('users', 'user_a')
        metadata_record   = self.non_service_metadataset_records[0]
        auth_headers      = self.apikey_auth(user)

        # post metadataset:
        metadataset_id = self.post_metadata(
            headers           = auth_headers,
            metadata_record   = metadata_record
        )["id"]["uuid"]

        # delete metdataset:
        _ = self.delete_metadata(
            headers           = auth_headers,
            metadataset_id=metadataset_id
        )

        # expect get for deleted metadataset to fail:
        _ = self.get_metadata(
            headers=auth_headers,
            metadataset_id=metadataset_id,
            expected_record=metadata_record,
            status=404
        )

    def test_announce_and_delete_file(self):
        """Test whether staged metadatasets can be deleted
        after staging"""
        self.fixture_manager.load_fixtureset('files_independent', database_insert=False)

        user = self.fixture_manager.get_fixture('users', 'user_a')
        # The following file is not staged since the fixture was loaded in without database insert
        file = self.fixture_manager.get_fixture('files_independent', 'user_a_file_1')

        auth_headers = self.apikey_auth(user)

        # announce file:
        file_upload_response = self.post_file(
            headers = auth_headers,
            name=file.name,
            checksum=file.checksum
        )

        # upload file to provided url:
        _ = self.upload_file(
            url_to_upload=file_upload_response["urlToUpload"],
            headers=file_upload_response["requestHeaders"],
            file_path=get_file_path(file.name),
            file_uuid=file_upload_response["id"]["uuid"],
            file_checksum=file.checksum,
        )

        # delete file:
        _ = self.delete_file(
            headers = auth_headers,
            file_id=file_upload_response["id"]["site"],
            file_uuid=file_upload_response["id"]["uuid"],
            file_checksum=file.checksum
        )

        # confirm that file info cannot be obtained anymore:
        _ = self.get_file(
            headers=auth_headers,
            file_id=file_upload_response["id"]["site"],
            status=404
        )

        # confirm that upload to original URL fails:
        _ = self.upload_file(
            url_to_upload=file_upload_response["urlToUpload"],
            headers=file_upload_response["requestHeaders"],
            file_path=get_file_path(file.name),
            file_uuid=file_upload_response["id"]["uuid"],
            file_checksum=file.checksum,
            status=404
        )
