"""Test major usage senarios related to staging and submission of
metadatasets and files.
"""

from . import BaseIntegrationTest, default_users
from .fixtures import UserFixture, AuthFixture
from typing import Optional

from datameta import models
from datameta.api import base_url

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

    
    def announce_file(
        self,
        auth:AuthFixture,
        name: str,
        checksum: str,
        status:int=200
    ):
        # request params:
        request_body = {
            "record": metadata_record
        }

        response = self.testapp.post_json(
            base_url + f"/files",
            headers=auth.header,
            params=request_body,
            status=status
        )

        if status==200:
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