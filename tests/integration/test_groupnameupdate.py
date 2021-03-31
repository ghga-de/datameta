"""Testing group name update via API request
"""

from . import BaseIntegrationTest
from datameta.api import base_url
class GroupNameUpdate(BaseIntegrationTest):

    def test_successful_admin_group_name_update(self, status:int=204):
        """Testing successful group name change by admin user.

        Expected Response:
            HTTP 204
        """
        user = self.users["admin"]
        request_body = {"name": "fancy_group_name"}

        response = self.testapp.put_json(
            base_url + f"/groups/group_x_id",
            headers = user.auth.header,
            params = request_body,
            status = status
        )

    def test_success_groupadmin_own_group_name_update(self, status:int=204):
        """Testing successful own group name change by group admin user.

        Expected Response:
            HTTP 204
        """
        user = self.users["group_x_admin"]
        request_body = {"name": "fancy_group_name"}

        response = self.testapp.put_json(
            base_url + f"/groups/group_x_id",
            headers = user.auth.header,
            params = request_body,
            status = status
        )

    def test_failure_groupadmin_other_group_name_update(self, status:int=403):
        """Testing unsuccessful other group name change by group admin user.

        Expected Response:
            HTTP 403
        """
        user = self.users["group_x_admin"]
        request_body = {"name": "fancy_group_name"}

        response = self.testapp.put_json(
            base_url + f"/groups/group_y_id",
            headers = user.auth.header,
            params = request_body,
            status = status
        )

    def test_failure_admin_invalid_group_name(self, status:int=403):
        """Testing unsuccessful group name update of invalid group.

        Expected Response:
            HTTP 403
        """
        user = self.users["admin"]
        request_body = {"name": "fancy_group_name"}

        response = self.testapp.put_json(
            base_url + f"/groups/duckburgh",
            headers = user.auth.header,
            params = request_body,
            status = status
        )
    

    def test_failure_own_group_name_update(self, status:int=403):
        """Testing unsuccessful own group name change by normal user.

        Expected Response:
            HTTP 403
        """
        user = self.users["user_a"]
        request_body = {"name": "fancy_group_name"}

        response = self.testapp.put_json(
            base_url + f"/groups/group_x_id",
            headers = user.auth.header,
            params = request_body,
            status = status
        )

    def test_failure_other_group_name_update(self, status:int=403):
        """Testing unsuccessful other group name change by normal user.

        Expected Response:
            HTTP 403
        """
        user = self.users["user_a"]
        request_body = {"name": "fancy_group_name"}

        response = self.testapp.put_json(
            base_url + f"/groups/group_y_id",
            headers = user.auth.header,
            params = request_body,
            status = status
        )

    def test_failure_group_name_update_not_authorised(self, status:int=401):
        """Testing unsuccessful group name change by unidentified, unauthorized user.

        Expected Response:
            HTTP 401
        """
        request_body = {"name": "fancy_group_name"}
        
        response = self.testapp.put_json(
            base_url + f"/groups/group_y_id",
            params = request_body,
            status = status
        )

    def test_failure_admin_group_name_update_expired_token(self, status:int=401):
        """Testing unsuccessful group name change by admin user with expired token.

        Expected Response:
            HTTP 401
        """
        user = self.users["admin"]
        request_body = {"name": "fancy_group_name"}

        response = self.testapp.put_json(
            base_url + f"/groups/group_x_id",
            headers = user.expired_auth.header,
            params = request_body,
            status = status
        )