"""Test major usage senarios related to staging and submission of
metadatasets and files.
"""

from . import BaseIntegrationTest, default_users
from .fixtures import UserFixture
from .utils import get_auth_headers
from typing import Optional

from datameta import models
from datameta.api import base_url

class TestStageAndSubmitSenario(BaseIntegrationTest):
    """
    Tests ApiKey creation, metadata staging, file staging, 
    """

    def post_key(
        self, 
        user:UserFixture,
        apikey_label:str="test_key", 
        status:int=200
    ):
        """Request ApiKey"""
        request_body = {
            "email": user.email,
            "password": user.password,
            "label": apikey_label
        }

        response = self.testapp.post_json(
            base_url + "/keys",
            params=request_body,
            status=status
        )

        return response.json

    def post_metadata(
        self,  
        token:str,
        metadata_record:dict,
        status:int=200,
):
        """Post metadataset"""
        # request params:
        request_headers = get_auth_headers(token)
        request_body = {
            "record": metadata_record
        }

        response = self.testapp.post_json(
            base_url + f"/metadatasets",
            headers=request_headers,
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
        token:str,
        metadataset_id:str,
        expected_record:Optional[dict]=None,
        status:int=200
    ):
        # request params:
        request_headers = get_auth_headers(token)

        response = self.testapp.get(
            base_url + f"/metadatasets/{metadataset_id}",
            headers=request_headers,
            status=status
        )

        if status==200:
            # check if response record contains same keys
            # as expected record (values might have changed
            # due to backend side processing):
            assert expected_record.keys() == response.json["record"].keys()
        
        return response.json


    def test_steps(self):
        # get fixtures:
        user = self.users["user_a"]
        metadata_records = self.metadata_records

        # get token
        user_session = self.post_key(user=user)
        token = user_session["token"]

        # post metadata:
        metadataset_ids = [
            self.post_metadata(
                token=token, 
                metadata_record=rec
            )["id"]["uuid"]
            for rec in metadata_records
        ]
        

        # get metadatasets and compare to original records:
        _ = [
            self.get_metadata(
                token=token, 
                metadataset_id=m_id,
                expected_record=metadata_records[idx]
            )
            for idx, m_id in enumerate(metadataset_ids)
        ]
