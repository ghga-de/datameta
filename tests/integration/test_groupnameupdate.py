"""Testing group name update via API request
"""
from parameterized import parameterized

from . import BaseIntegrationTest
from datameta.api import base_url

class GroupNameUpdate(BaseIntegrationTest):

    @parameterized.expand([
        # TEST_NAME                    EXEC_USER           TARGET_GRP       RESP
        ("foreign_as_admin"          , "admin"           , "group_x_id"   , 204),
        ("own_as_group_admin"        , "group_x_admin"   , "group_x_id"   , 403),
        ("foreign_as_group_admin"    , "group_x_admin"   , "group_y_id"   , 403),
        ("invalid_group"             , "admin"           , "duckburgh"    , 403),
        ("own_as_regular_user"       , "user_a"          , "group_x_id"   , 403),
        ("foreign_as_regular_user"   , "user_a"          , "group_y_id"   , 403)
        ])
    def test_group_name_update(self, _, executing_user:str, target_group_id:str, expected_response:int):
        user = self.users[executing_user]
        request_body = {"name": "new_group_name"}

        response = self.testapp.put_json(
            f"{base_url}/groups/{target_group_id}",
            headers = user.auth.header,
            params = request_body,
            status = expected_response
        )

    def test_failure_group_name_update_not_authorised(self, status:int=401):
        """Testing unsuccessful group name change by unidentified, unauthorized user.

        Expected Response:
            HTTP 401
        """
        request_body = {"name": "fancy_group_name"}

        response = self.testapp.put_json(
            f"{base_url}/groups/group_y_id",
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
            f"{base_url}/groups/group_x_id",
            headers = user.expired_auth.header,
            params = request_body,
            status = status
        )
