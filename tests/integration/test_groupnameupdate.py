"""Testing group name update via API request
"""

from . import BaseIntegrationTest
from .utils import get_auth_headers
from datameta.api import base_url

class GroupNameUpdate(BaseIntegrationTest):

    def test_successful_admin_group_name_update(self, status:int=204):
        token = self.get_api_key("admin", base_url)
        request_headers = get_auth_headers(token)
        
        request_body = {"name": "fancy_group_name"}

        response = self.testapp.put_json(
            base_url + f"/groups/group_x_id",
            headers = request_headers,
            params = request_body,
            status=status
        )

    def test_failure_groupadmin_own_group_name_update(self, status:int=403):
        token = self.get_api_key("group_x_admin", base_url)
        request_headers = get_auth_headers(token)
        
        request_body = {"name": "fancy_group_name"}

        response = self.testapp.put_json(
            base_url + f"/groups/group_x_id",
            headers = request_headers,
            params = request_body,
            status=status
        )

    def test_failure_groupadmin_other_group_name_update(self, status:int=403):
        token = self.get_api_key("group_x_admin", base_url)
        request_headers = get_auth_headers(token)
        
        request_body = {"name": "fancy_group_name"}

        response = self.testapp.put_json(
            base_url + f"/groups/group_y_id",
            headers = request_headers,
            params = request_body,
            status=status
        )
    

    def test_failure_own_group_name_update(self, status:int=403):
        token = self.get_api_key("user_a", base_url)
        request_headers = get_auth_headers(token)

        request_body = {"name": "fancy_group_name"}

        response = self.testapp.put_json(
            base_url + f"/groups/group_x_id",
            headers = request_headers,
            params = request_body,
            status=status
        )

    def test_failure_other_group_name_update(self, status:int=403):
        token = self.get_api_key("user_a", base_url)
        request_headers = get_auth_headers(token)

        request_body = {"name": "fancy_group_name"}

        response = self.testapp.put_json(
            base_url + f"/groups/group_y_id",
            headers = request_headers,
            params = request_body,
            status = status
        )

    def test_failure_group_name_update_not_authorised(self, status:int=401):
        request_body = {"name": "fancy_group_name"}
        
        response = self.testapp.put_json(
            base_url + f"/groups/group_y_id",
            params = request_body,
            status=status
        )