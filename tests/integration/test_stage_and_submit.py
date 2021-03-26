"""Test major usage senarios related to staging and submission of
metadatasets and files.
"""

from . import BaseIntegrationTest, default_users
from .utils import get_auth_headers
from typing import Optional

from datameta import models
from datameta.api import base_url

class TestStageAndSubmitSenario(BaseIntegrationTest):
    """
    Tests ApiKey creation, metadata staging, file staging, 
    """

    def step_1_post_key(self, status:int=200, apikey_label:str="test_key"):
        """Request ApiKey"""
        request_body = {
            "email": self.state["user"].email,
            "password": self.state["user"].password,
            "label": apikey_label
        }

        response = self.testapp.post_json(
            base_url + "/keys",
            params=request_body,
            status=status
        )

        if status==200:
            self.state["apikey_token"] = response.json["token"]

    def step_2_post_metadata(
        self, 
        status:int=200, 
        metadata_record:Optional[dict]=None
    ):
        """Post metadataset"""
        if not metadata_record:
            metadata_record = self.metadata_records[0]

        # request params:
        request_headers = get_auth_headers(self.state["apikey_token"])
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
            # store response in state:
            self.state["metadata_id"] = response.json["id"]["site"]

    def test_steps(self):
        # set initial state:
        self.state = {
            "user": self.users["user_a"],
            "apikey_token": None, # slot to store the apikey
            "metadata_ids": [], # slot to store metadata ids
            "file_ids": [], # slot to store file ids
        }

        # execute all test steps:
        # - create apikey
        # - post metadata record
        self._test_all_steps()