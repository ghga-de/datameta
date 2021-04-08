"""Testing user management via API request
"""
from parameterized import parameterized

from . import BaseIntegrationTest, default_users
from datameta import models
from datameta.api import base_url

from .utils import get_user, get_group
class TestUserManagement(BaseIntegrationTest):

    @parameterized.expand([
        ("self_name_change", "user_a", "", "changed_by_user_a", 204),
        ("other_name_change_by_regular_user", "user_a", "user_c", "changed_by_user_a", 403),
        ("other_name_change_by_own_group_admin", "group_x_admin", "user_a", "changed_by_group_x_admin", 204),
        ("other_name_change_by_other_group_admin", "group_x_admin", "user_c", "changed_by_group_x_admin", 403),
        ("other_name_change_by_admin", "admin", "user_a", "changed_by_admin", 204),
    ])
    def xxtest_name_change(self, testname:str, executing_user:str, target_user:str, new_name:str, expected_response:int):
        user = self.users[executing_user]
        target_user = self.users[target_user] if target_user else user

        request_body = {
            "name": new_name
        }

        req_json = {
            "headers": user.auth.header,
            "params": request_body,
            "status": expected_response
        }

        response = self.testapp.put_json(
            f"{base_url}/users/{target_user.uuid}",
            **req_json
        )

        db_user = get_user(self.session_factory, target_user)
        expected_outcome = any([
            expected_response == 204 and db_user["fullname"] == new_name,
            expected_response == 403 and db_user["fullname"] == target_user.fullname
        ])
        
        assert expected_outcome, f"{testname} failed: {db_user['fullname']} != {new_name} {expected_response}."

    @parameterized.expand([
        ("self_group_change", "user_a", "", "group_y", 403),
        ("self_group_change_by_group_admin", "group_x_admin", "", "group_y", 403),
        ("other_group_change_by_group_admin", "group_x_admin", "user_a", "group_y", 403),
        ("other_group_change_by_other_group_admin", "group_x_admin", "user_c", "group_x", 403),
        ("self_group_change_by_admin", "admin", "", "group_y", 204),
    ])
    def xxtest_group_change(self, testname:str, executing_user:str, target_user:str, new_group:str, expected_response:int):

        def make_request(session_factory, user, target_user, new_group_uuid, expected_response):
            req_json = {
                "headers": user.auth.header,
                "params": {
                    "groupId": new_group_uuid
                },
                "status": expected_response
            }

            response = self.testapp.put_json(
                f"{base_url}/users/{target_user.uuid}",
                **req_json
            )

            db_user = get_user(session_factory, target_user)
            expected_outcome = any([
                expected_response == 204 and db_user["group_uuid"] == new_group_uuid,
                expected_response == 403 and db_user["group_uuid"] != new_group_uuid
            ])
        
            assert expected_outcome, f"{testname} failed: {db_user['group_uuid']==new_group_uuid} {expected_response}."
            

        user = self.users[executing_user]
        target_user = self.users[target_user] if target_user else user

        new_group_uuid = str(get_group(self.session_factory, new_group))
        current_group_uuid = str(get_group(self.session_factory, target_user.groupname))
        make_request(self.session_factory, user, target_user, new_group_uuid, expected_response)

        if expected_response == 204:
            make_request(self.session_factory, user, target_user, current_group_uuid, expected_response)
        
    @parameterized.expand([
        ("self_regular_user_grant_site_admin", "user_a", "", ("+siteAdmin",), 403),
        ("other_regular_user_revoke_site_admin_from_admin", "user_a", "admin", ("-siteAdmin",), 403),
        ("other_group_admin_grant_group_admin_to_regular", "group_x_admin", "user_a", ("+groupAdmin",), 204),
        ("self_group_admin_grant_site_admin", "group_x_admin", "", ("+siteAdmin",), 403),
        ("other_group_admin_grant_site_admin_to_regular", "group_x_admin", "user_a", ("+siteAdmin",), 403),
        ("other_group_admin_revoke_site_admin_from_admin", "group_x_admin", "admin", ("-siteAdmin",), 403),
        ("other_site_admin_grant_admins_to_regular", "admin", "user_a", ("+siteAdmin", "+groupAdmin"), 204),
        ("xother_site_admin_revoke_admins_from_regular", "admin", "user_a", ("-siteAdmin", "-groupAdmin"), 204),
    ])
    def test_status_changes(self, testname:str, executing_user:str, target_user:str, actions:tuple, expected_response:int):

        def make_request(session_factory, user, target_user, actions, expected_response):
            req_json = {
                "headers": user.auth.header,
                "status": expected_response
            }
            for action in actions:
                req_json.setdefault("params", dict())[action[1:]] = action[0] == "+"

            response = self.testapp.put_json(
                f"{base_url}/users/{target_user.uuid}",
                **req_json
            )
        
            db_user = get_user(session_factory, target_user)

            expected_outcome = any([
                expected_response == 204 and all(val == db_user[key] for key, val in req_json["params"].items()),
                expected_response == 403 and all(val != db_user[key] for key, val in req_json["params"].items()),
            ])
        
            assert expected_outcome, f"{testname} failed: {response} {expected_outcome} {expected_response} {req_json['params']} {db_user}."


        user = self.users[executing_user]
        target_user = self.users[target_user] if target_user else user

        if testname.startswith("x"):
            db_user = get_user(self.session_factory, target_user)
            assert db_user['groupAdmin'], f"{db_user}"

        make_request(self.session_factory, user, target_user, actions, expected_response)
        #TODO undo 204s
    
    
    def step_3l(self, status:int=204):
        """admin: remove admin status of user_a"""

        request_body = {
            "siteAdmin": False,
            "groupAdmin": False
        }

        response = self.testapp.put_json(
            base_url + "/users/" + self.state["user_a"].uuid,
            headers=self.state["admin"].auth.header,
            params=request_body,
            status=status
        )

    def step_3m(self, status:int=200):
        """Check if the previous admin status change worked"""

        response = self.testapp.get(
            "/api/admin",
            headers=self.state["admin"].auth.header,
            status=status
        )

        if status==200: # check, if the admin status change worked

            for user in response.json["users"]:
                if user["id"]["uuid"] == self.state["user_a"].uuid:
                    assert user["group_admin"] == False, (
                        "The group_admin status removal of user_a did not work."
                    )
                    assert user["site_admin"] == False, (
                        "The site_admin status removal of user_a did not work."
                    )
                    

    def step_4a(self, status:int=403):
        """user_a: disable user_a"""

        request_body = {
            "enabled": False
        }

        response = self.testapp.put_json(
            base_url + "/users/" + self.state["user_a"].uuid,
            headers=self.state["user_a"].auth.header,
            params=request_body,
            status=status
        )

    def step_4b(self, status:int=403):
        """user_a: enable user_a"""

        request_body = {
            "enabled": False
        }

        response = self.testapp.put_json(
            base_url + "/users/" + self.state["user_a"].uuid,
            headers=self.state["user_a"].auth.header,
            params=request_body,
            status=status
        )

    def step_4c(self, status:int=204):
        """group_x_admin: disable user_a"""

        request_body = {
            "enabled": False
        }

        response = self.testapp.put_json(
            base_url + "/users/" + self.state["user_a"].uuid,
            headers=self.state["group_x_admin"].auth.header,
            params=request_body,
            status=status
        )

    def step_4d(self, status:int=200):
        """Check if the previous enable status change worked"""

        response = self.testapp.get(
            "/api/admin",
            headers=self.state["admin"].auth.header,
            status=status
        )

        if status==200: # check, if the enabled status change worked

            for user in response.json["users"]:
                if user["id"]["uuid"] == self.state["user_a"].uuid:
                    assert user["enabled"] == False, (
                        "The enable status change did not work."
                    )

    def step_4e(self, status:int=204):
        """group_x_admin: enable user_a"""

        request_body = {
            "enabled": True
        }

        response = self.testapp.put_json(
            base_url + "/users/" + self.state["user_a"].uuid,
            headers=self.state["group_x_admin"].auth.header,
            params=request_body,
            status=status
        )

    def step_4f(self, status:int=200):
        """Check if the previous enable status change worked"""

        response = self.testapp.get(
            "/api/admin",
            headers=self.state["admin"].auth.header,
            status=status
        )

        if status==200: # check, if the enabled status change worked

            for user in response.json["users"]:
                if user["id"]["uuid"] == self.state["user_a"].uuid:
                    assert user["enabled"] == True, (
                        "The enable status change did not work."
                    )

    def step_4g(self, status:int=204):
        """admin: make user_b a site_admin"""

        request_body = {
            "siteAdmin": False
        }

        response = self.testapp.put_json(
            base_url + "/users/" + self.state["user_b"].uuid,
            headers=self.state["admin"].auth.header,
            params=request_body,
            status=status
        )

    #ToDo: This should not be possible. Change, once it has been changed in code
    def step_4h(self, status:int=204):
        """group_x_admin: disable user_b which is a site_admin"""

        request_body = {
            "enabled": False
        }

        response = self.testapp.put_json(
            base_url + "/users/" + self.state["user_b"].uuid,
            headers=self.state["group_x_admin"].auth.header,
            params=request_body,
            status=status
        )

    #ToDo: This should not be possible. Change, once it has been changed in code
    def step_4i(self, status:int=200):
        """Check if the previous enable status change worked"""

        response = self.testapp.get(
            "/api/admin",
            headers=self.state["admin"].auth.header,
            status=status
        )

        if status==200: # check, if the enabled status change worked

            for user in response.json["users"]:
                if user["id"]["uuid"] == self.state["user_b"].uuid:
                    assert user["enabled"] == False, (
                        "The enable status change did not work."
                    )

    def step_4j(self, status:int=403):
        """group_x_admin: disable user_c which is not in group_x"""

        request_body = {
            "enabled": False
        }

        response = self.testapp.put_json(
            base_url + "/users/" + self.state["user_c"].uuid,
            headers=self.state["group_x_admin"].auth.header,
            params=request_body,
            status=status
        )

    def step_4k(self, status:int=204):
        """admin: re-enable user_b which is a site_admin"""

        request_body = {
            "enabled": True
        }

        response = self.testapp.put_json(
            base_url + "/users/" + self.state["user_b"].uuid,
            headers=self.state["admin"].auth.header,
            params=request_body,
            status=status
        )

    def step_4l(self, status:int=200):
        """Check if the previous enable status change worked"""

        response = self.testapp.get(
            "/api/admin",
            headers=self.state["admin"].auth.header,
            status=status
        )

        if status==200: # check, if the enabled status change worked

            for user in response.json["users"]:
                if user["id"]["uuid"] == self.state["user_b"].uuid:
                    assert user["enabled"] == True, (
                        "The enable status change did not work."
                    )