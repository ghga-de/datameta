"""Testing group name update via API request
"""
from parameterized import parameterized

from . import BaseIntegrationTest
from datameta.api import base_url

class GroupNameUpdate(BaseIntegrationTest):

    @parameterized.expand([
        # TEST_NAME                    EXEC_USER           TARGET_GRP       NEW_GROUPNAME    RESP
        ("foreign_as_admin"            , "admin"           , "group_x_id"   , "fancy_group"  , 204),
        ("own_as_group_admin"          , "group_x_admin"   , "group_x_id"   , "fancy_group"  , 403),
        ("foreign_as_group_admin"      , "group_x_admin"   , "group_y_id"   , "fancy_group"  , 403),
        ("invalid_group"               , "admin"           , "duckburgh"    , "fancy_group"  , 403),
        ("own_as_regular_user"         , "user_a"          , "group_x_id"   , "fancy_group"  , 403),
        ("foreign_as_regular_user"     , "user_a"          , "group_y_id"   , "fancy_group"  , 403),
        ("admin_use_existing_groupname", "admin"           , "group_x_id"   , "group_y"      , 400),
        ("unauthorized"                , ""                , "group_x_id"   , "fancy_group"  , 401),
        ("admin_expired_token"         , "admin:expired"   , "group_x_id"   , "fancy_group"  , 401),
        ])
    def test_group_name_update(self, _, executing_user:str, target_group_id:str, new_groupname:str, expected_response:int):
        req_json = {
            "status": expected_response,
            "params": {"name": new_groupname}
        }
        if executing_user:
            executing_user, *is_expired = executing_user.split(":")
            user = self.default_users[executing_user]
            req_json["headers"] = user.expired_auth.header if is_expired else user.auth.header

        response = self.testapp.put_json(
            f"{base_url}/groups/{target_group_id}",
            **req_json
        )
