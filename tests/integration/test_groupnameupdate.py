"""Testing group name update via API request
"""
from parameterized import parameterized

from . import BaseIntegrationTest
from .utils import get_auth_header
from datameta.api import base_url


class GroupNameUpdate(BaseIntegrationTest):

    def setUp(self):
        super().setUp()
        self.fixture_manager.load_fixtureset('groups')
        self.fixture_manager.load_fixtureset('users')
        self.fixture_manager.load_fixtureset('apikeys')

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
        ("admin_expired_token"         , "admin: expired"   , "group_x_id"   , "fancy_group"  , 401),
        ])
    def test_group_name_update(self, _, executing_user: str, target_group_id: str, new_groupname: str, expected_response: int):
        req_args = {
            "status": expected_response,
            "params": {"name": new_groupname}
        }
        if executing_user:
            executing_user, *is_expired = executing_user.split(":")
            apikey = self.fixture_manager.get_fixture("apikeys", executing_user + ("_expired" if is_expired else ""))
            req_args["headers"] = get_auth_header(apikey.value_plain)

        self.testapp.put_json(
            f"{base_url}/groups/{target_group_id}",
            **req_args
        )
