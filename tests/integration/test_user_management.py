"""Testing user management via API request
"""
from parameterized import parameterized

from . import BaseIntegrationTest, default_users
from datameta import models
from datameta.api import base_url

from .utils import get_user_by_uuid, get_group_by_name
class TestUserManagement(BaseIntegrationTest):

    def do_request(self, user_uuid, **params):
        response = self.testapp.put_json(
            f"{base_url}/users/{user_uuid}",
            **params
        )
        return response

    def process_name_change_request(self, testname, user, target_user, new_name, expected_response):
        response = self.do_request(target_user.uuid, status=expected_response, headers=user.auth.header, params={"name": new_name})

        db_user = get_user_by_uuid(self.session_factory, target_user.uuid)
        expected_outcome = any([
            expected_response == 204 and db_user["fullname"] == new_name,
            expected_response == 403 and db_user["fullname"] == target_user.fullname
        ])
        
        assert expected_outcome, f"{testname} failed"

    def process_group_change_request(self, testname, user, target_user, new_group_uuid, expected_response):
        response = self.do_request(target_user.uuid, status=expected_response, headers=user.auth.header, params={"groupId": new_group_uuid})

        db_user = get_user_by_uuid(self.session_factory, target_user.uuid)
        expected_outcome = any([
            expected_response == 204 and db_user["group_uuid"] == new_group_uuid,
            expected_response == 403 and db_user["group_uuid"] != new_group_uuid
        ])

        assert expected_outcome, f"{testname} failed."

    def process_status_change_request(self, testname, user, target_user, actions, expected_response, is_undo=False):
        unmod_user = get_user_by_uuid(self.session_factory, target_user.uuid)

        params = dict()
        for action in actions:
            value = (action[0] == "+") if not is_undo else (action[0] != "+")
            params[action[1:]] = value

        response = self.do_request(target_user.uuid, status=expected_response, headers=user.auth.header, params=params)

        db_user = get_user_by_uuid(self.session_factory, target_user.uuid)
        expected_outcome = any([
            expected_response == 204 and all(val == db_user[key] for key, val in params.items()),
            expected_response == 403 and all((val != db_user[key] or val == unmod_user[key]) for key, val in params.items()),
        ])

        assert expected_outcome, f"{testname} failed."



    @parameterized.expand([
        ("self_name_change", "user_a", "", "changed_by_user_a", 204),
        ("other_name_change_by_regular_user", "user_a", "user_c", "changed_by_user_a", 403),
        ("other_name_change_by_own_group_admin", "group_x_admin", "user_a", "changed_by_group_x_admin", 204),
        ("other_name_change_by_other_group_admin", "group_x_admin", "user_c", "changed_by_group_x_admin", 403),
        ("other_name_change_by_admin", "admin", "user_a", "changed_by_admin", 204),
    ])
    def test_name_change(self, testname:str, executing_user:str, target_user:str, new_name:str, expected_response:int):
        user = self.default_users[executing_user]
        target_user = self.default_users[target_user] if target_user else user

        self.process_name_change_request(testname, user, target_user, new_name, expected_response)

    @parameterized.expand([
        ("self_group_change"                         , "user_a"          , None       , "group_y"   , 403),
        ("self_group_change_by_group_admin"          , "group_x_admin"   , None       , "group_y"   , 403),
        ("other_group_change_by_group_admin"         , "group_x_admin"   , "user_a"   , "group_y"   , 403),
        ("other_group_change_by_other_group_admin"   , "group_x_admin"   , "user_c"   , "group_x"   , 403),
        ("self_group_change_by_admin"                , "admin"           , None       , "group_y"   , 204),
    ])
    def test_group_change(self, testname:str, executing_user:str, target_user:str, new_group:str, expected_response:int):
        user : models.User             = self.default_users[executing_user]
        db_target_user : models.User   = self.default_users[target_user] if target_user else user
        new_group_uuid                 = str(get_group_by_name(self.session_factory, new_group))
        current_group_uuid             = str(get_group_by_name(self.session_factory, db_target_user.groupname))

        self.process_group_change_request(testname, user, db_target_user, new_group_uuid, expected_response)

        if expected_response == 204:
            self.process_group_change_request(testname, user, db_target_user, current_group_uuid, expected_response)
        
    @parameterized.expand([
        ("self_regular_user_grant_site_admin", "user_a", "", ("+siteAdmin",), 403),
        ("other_regular_user_revoke_site_admin_from_admin", "user_a", "admin", ("-siteAdmin",), 403),
        ("other_group_admin_grant_group_admin_to_regular", "group_x_admin", "user_a", ("+groupAdmin",), 204),
        ("self_group_admin_grant_site_admin", "group_x_admin", "", ("+siteAdmin",), 403),
        ("other_group_admin_grant_site_admin_to_regular", "group_x_admin", "user_a", ("+siteAdmin",), 403),
        ("other_group_admin_revoke_site_admin_from_admin", "group_x_admin", "admin", ("-siteAdmin",), 403),
        ("other_site_admin_grant_admins_to_regular", "admin", "user_a", ("+siteAdmin", "+groupAdmin"), 204),
        ("self_disable_regular_user", "user_a", "", ("-enabled",), 403),
        ("self_enable_regular_user", "user_a", "", ("+enabled",), 403),
        ("other_disable_regular_user", "group_x_admin", "user_a", ("-enabled",), 204),
        ("other_disable_regular_user_other_group", "group_x_admin", "user_c", ("-enabled",), 403),
        ("self_regular_user_grant_site_read", "user_a", "", ("+siteRead",), 403),
        ("other_group_admin_grant_site_read_to_regular", "group_x_admin", "user_a", ("+siteRead",), 403),
        ("other_site_admin_grant_site_read_to_regular", "admin", "user_a", ("+siteRead",), 204),
    ])
    def test_status_changes(self, testname:str, executing_user:str, target_user:str, actions:tuple, expected_response:int):
        user = self.default_users[executing_user]
        target_user = self.default_users[target_user] if target_user else user
        self.process_status_change_request(testname, user, target_user, actions, expected_response)

        if expected_response == 204:
            self.process_status_change_request(testname, user, target_user, actions, expected_response, is_undo=True)
        

    def test_edgecase_status_changes(self):
        admin = self.default_users["admin"]
        user_b = self.default_users["user_b"]
        group_x_admin = self.default_users["group_x_admin"]

        """admin: make user_b a site_admin"""
        self.do_request(user_b.uuid, status=204, headers=admin.auth.header, params={"siteAdmin": True})

        """group_x_admin: disable user_b which is a site_admin"""
        self.do_request(user_b.uuid, status=403, headers=group_x_admin.auth.header, params={"enabled": False})

        """admin: re-enable user_b which is a site_admin"""
        self.do_request(user_b.uuid, status=204, headers=admin.auth.header, params={"enabled": True})
