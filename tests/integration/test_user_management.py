"""Tests user management for the API
    +: Changes that should work
    -: Changes that should not work
"""

"""Test 1: Namechange
a) user_a:
    + change name of user_a
    - change name of user_c
b) group_x_admin:
    + change name of user_a
    - change name of user_c
c) admin:
    + change name of user_a
"""

"""Test 2: Group Change
a) user_a:
    - change group of user_a
b) group_x_admin:
    - change group of group_x_admin
    - change group of user_a
    - change group of user_c to group_x
c) admin:
    + change group of admin
    + change group of user_a
"""

"""Test 3: Admin settings change
a) user_a:
    - make user_a admin
    - remove admin status of admin
b) group_x_admin:
    + make user_a group_admin
    + remove user_a as group_admin
    - make group_x_admin site admin
    - make user_a site admin
    - remove admin status of admin
c) admin:
    + make user_a group & site admin 
    + remove admin status of user_a
"""

"""Test 4: Enabled settings change:
Note, that the enabled setting currently does not do anything. Once this changes, these tests have to be expanded
a) user_a:
    - disable/enable user_a
b) group_x_admin:
    + disable/enable user_a
    - (admin: make user_b site admin) disable/enable user_b
    - disable/enable user_c
c) admin:
    + disable/enable user_b
"""

from . import BaseIntegrationTest, default_users

from datameta import models
from datameta.api import base_url

class TestUserManagement(BaseIntegrationTest):

    def step_0(self, status:int=200):
        """Setup: Request list of all groups"""

        response = self.testapp.get(
            "/api/admin",
            headers=self.state["admin"].auth.header,
            status=status
        )

        if status==200: # check, if the name change did work
            self.state["groups"] = response.json["groups"]


    def step_1a(self, status:int=204):
        """user_a: change name of user_a"""

        self.state["user_name_change_to"] = "changed_by_user_a"

        request_body = {
            "name": self.state["user_name_change_to"]
        }

        response = self.testapp.put_json(
            base_url + "/users/" + self.state["user_a"].uuid,
            headers=self.state["user_a"].auth.header,
            params=request_body,
            status=status
        )

    def step_1b(self, status:int=200):
        """Check if the previous name change did happen"""

        response = self.testapp.get(
            "/api/admin",
            headers=self.state["admin"].auth.header,
            status=status
        )

        if status==200: # check, if the name change did work
            
            for user in response.json["users"]:
                if user["id"]["uuid"] == self.state["user_a"].uuid:
                    assert user["fullname"] == self.state["user_name_change_to"], (
                        "The name change did not work."
                    )

    def step_1c(self, status:int=403):
        """user_a: change name of user_c"""

        self.state["user_name_change_to"] = "changed_by_user_a"

        request_body = {
            "name": self.state["user_name_change_to"]
        }

        response = self.testapp.put_json(
            base_url + "/users/" + self.state["user_c"].uuid,
            headers=self.state["user_a"].auth.header,
            params=request_body,
            status=status
        )

    def step_1d(self, status:int=204):
        """group_x_admin: change name of user_a"""
        
        self.state["user_name_change_to"] = "changed_by_group_x_admin"

        request_body = {
            "name": self.state["user_name_change_to"]
        }

        response = self.testapp.put_json(
            base_url + "/users/" + self.state["user_a"].uuid,
            headers=self.state["group_x_admin"].auth.header,
            params=request_body,
            status=status
        )

    def step_1f(self, status:int=200):
        """Check if the previous name change did happen"""

        response = self.testapp.get(
            "/api/admin",
            headers=self.state["admin"].auth.header,
            status=status
        )

        if status==200: # check, if the name change did work
            
            for user in response.json["users"]:
                if user["id"]["uuid"] == self.state["user_a"].uuid:
                    assert user["fullname"] == self.state["user_name_change_to"], (
                        "The name change did not work."
                    )

    def step_1g(self, status:int=403):
        """group_x_admin: change name of user_c"""

        self.state["user_name_change_to"] = "changed_by_group_x_admin"

        request_body = {
            "name": self.state["user_name_change_to"]
        }

        response = self.testapp.put_json(
            base_url + "/users/" + self.state["user_c"].uuid,
            headers=self.state["group_x_admin"].auth.header,
            params=request_body,
            status=status
        )

    def step_1h(self, status:int=204):
        """admin: change name of user_a"""

        self.state["user_name_change_to"] = "changed_by_admin"

        request_body = {
            "name": self.state["user_name_change_to"]
        }

        response = self.testapp.put_json(
            base_url + "/users/" + self.state["user_a"].uuid,
            headers=self.state["admin"].auth.header,
            params=request_body,
            status=status
        )

    def step_1i(self, status:int=200):
        """Check if the previous name change did happen"""

        response = self.testapp.get(
            "/api/admin",
            headers=self.state["admin"].auth.header,
            status=status
        )

        if status==200: # check, if the name change did work
            
            for user in response.json["users"]:
                if user["id"]["uuid"] == self.state["user_a"].uuid:
                    assert user["fullname"] == self.state["user_name_change_to"], (
                        "The name change did not work."
                    )


    def step_2a(self, status:int=403):
        """user_a: change group of user_a"""
        
        new_group_name = self.state["user_c"].groupname
        new_group_id = None
        
        for group in self.state["groups"]:
            if group["name"] == new_group_name:
                new_group_id = group["id"]["uuid"]


        request_body = {
            "groupId": new_group_id
        }

        response = self.testapp.put_json(
            base_url + "/users/" + self.state["user_a"].uuid,
            headers=self.state["user_a"].auth.header,
            params=request_body,
            status=status
        )

    def step_2b(self, status:int=403):
        """group_x_admin: change group of group_x_admin"""
        
        new_group_name = self.state["user_c"].groupname
        new_group_id = None
        
        for group in self.state["groups"]:
            if group["name"] == new_group_name:
                new_group_id = group["id"]["uuid"]


        request_body = {
            "groupId": new_group_id
        }

        response = self.testapp.put_json(
            base_url + "/users/" + self.state["group_x_admin"].uuid,
            headers=self.state["group_x_admin"].auth.header,
            params=request_body,
            status=status
        )

    def step_2c(self, status:int=403):
        """group_x_admin: change group of user_a"""
        
        new_group_name = self.state["user_c"].groupname
        new_group_id = None
        
        for group in self.state["groups"]:
            if group["name"] == new_group_name:
                new_group_id = group["id"]["uuid"]


        request_body = {
            "groupId": new_group_id
        }

        response = self.testapp.put_json(
            base_url + "/users/" + self.state["user_a"].uuid,
            headers=self.state["group_x_admin"].auth.header,
            params=request_body,
            status=status
        )

    def step_2d(self, status:int=403):
        """group_x_admin: change group of user_c"""
        
        new_group_name = self.state["user_a"].groupname
        new_group_id = None
        
        for group in self.state["groups"]:
            if group["name"] == new_group_name:
                new_group_id = group["id"]["uuid"]


        request_body = {
            "groupId": new_group_id
        }

        response = self.testapp.put_json(
            base_url + "/users/" + self.state["user_c"].uuid,
            headers=self.state["group_x_admin"].auth.header,
            params=request_body,
            status=status
        )

    def step_2e(self, status:int=204):
        """admin: change group of user_a"""
        
        new_group_name = self.state["user_c"].groupname
        new_group_id = None
        
        for group in self.state["groups"]:
            if group["name"] == new_group_name:
                new_group_id = group["id"]["uuid"]


        request_body = {
            "groupId": new_group_id
        }

        response = self.testapp.put_json(
            base_url + "/users/" + self.state["user_a"].uuid,
            headers=self.state["admin"].auth.header,
            params=request_body,
            status=status
        )

    def step_2f(self, status:int=204):
        """admin: change group of admin"""
        
        new_group_name = self.state["user_c"].groupname
        new_group_id = None
        
        for group in self.state["groups"]:
            if group["name"] == new_group_name:
                new_group_id = group["id"]["uuid"]


        request_body = {
            "groupId": new_group_id
        }

        response = self.testapp.put_json(
            base_url + "/users/" + self.state["admin"].uuid,
            headers=self.state["admin"].auth.header,
            params=request_body,
            status=status
        )

    def step_2g(self, status:int=200):
        """Check if the previous group changes did happen"""

        response = self.testapp.get(
            "/api/admin",
            headers=self.state["admin"].auth.header,
            status=status
        )

        if status==200: # check, if the name change did work
            
            for user in response.json["groups"]:
                if user["id"]["uuid"] == self.state["user_a"].uuid:
                    assert user["group_name"] == "group_y", (
                        "The group change of user_a did not work."
                    )
                if user["id"]["uuid"] == self.state["admin"].uuid:
                    assert user["group_name"] == "group_y", (
                        "The group change of admin did not work."
                    )

    def step_2h(self, status:int=204):
        """admin: change group of user_a back to group_x"""
        
        new_group_name = self.state["user_a"].groupname
        new_group_id = None
        
        for group in self.state["groups"]:
            if group["name"] == new_group_name:
                new_group_id = group["id"]["uuid"]


        request_body = {
            "groupId": new_group_id
        }

        response = self.testapp.put_json(
            base_url + "/users/" + self.state["user_a"].uuid,
            headers=self.state["admin"].auth.header,
            params=request_body,
            status=status
        )

    def step_2i(self, status:int=204):
        """admin: change group of admin back to admin"""
        
        new_group_name = self.state["admin"].groupname
        new_group_id = None
        
        for group in self.state["groups"]:
            if group["name"] == new_group_name:
                new_group_id = group["id"]["uuid"]


        request_body = {
            "groupId": new_group_id
        }

        response = self.testapp.put_json(
            base_url + "/users/" + self.state["admin"].uuid,
            headers=self.state["admin"].auth.header,
            params=request_body,
            status=status
        )


    def step_3a(self, status:int=403):
        """user_a: make user_a site_admin"""

        request_body = {
            "siteAdmin": True
        }

        response = self.testapp.put_json(
            base_url + "/users/" + self.state["user_a"].uuid,
            headers=self.state["user_a"].auth.header,
            params=request_body,
            status=status
        )

    def step_3b(self, status:int=403):
        """user_a: remove site_admin status of admin"""

        request_body = {
            "siteAdmin": False
        }

        response = self.testapp.put_json(
            base_url + "/users/" + self.state["admin"].uuid,
            headers=self.state["user_a"].auth.header,
            params=request_body,
            status=status
        )

    def step_3c(self, status:int=204):
        """group_x_admin: make user_a group_admin"""

        request_body = {
            "groupAdmin": True
        }

        response = self.testapp.put_json(
            base_url + "/users/" + self.state["user_a"].uuid,
            headers=self.state["group_x_admin"].auth.header,
            params=request_body,
            status=status
        )

    def step_3d(self, status:int=200):
        """Check if the previous admin status change worked"""

        response = self.testapp.get(
            "/api/admin",
            headers=self.state["admin"].auth.header,
            status=status
        )

        if status==200: # check, if the admin status change worked
            
            for user in response.json["users"]:
                if user["id"]["uuid"] == self.state["user_a"].uuid:
                    assert user["group_admin"] == True, (
                        "The admin status change did not work."
                    )

    def step_3e(self, status:int=204):
        """group_x_admin: remove user_a as group_admin"""

        request_body = {
            "groupAdmin": False
        }


        response = self.testapp.put_json(
            base_url + "/users/" + self.state["user_a"].uuid,
            headers=self.state["group_x_admin"].auth.header,
            params=request_body,
            status=status
        )

    def step_3f(self, status:int=200):
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
                        "The admin status change did not work."
                    )

    def step_3g(self, status:int=403):
        """group_x_admin: make group_x_admin site_admin"""

        request_body = {
            "siteAdmin": True
        }

        response = self.testapp.put_json(
            base_url + "/users/" + self.state["group_x_admin"].uuid,
            headers=self.state["group_x_admin"].auth.header,
            params=request_body,
            status=status
        )

    def step_3h(self, status:int=403):
        """group_x_admin: make user_a site_admin"""

        request_body = {
            "siteAdmin": True
        }

        response = self.testapp.put_json(
            base_url + "/users/" + self.state["user_a"].uuid,
            headers=self.state["group_x_admin"].auth.header,
            params=request_body,
            status=status
        )

    def step_3i(self, status:int=403):
        """group_x_admin: remove admin status of admin"""

        request_body = {
            "siteAdmin": False
        }

        response = self.testapp.put_json(
            base_url + "/users/" + self.state["admin"].uuid,
            headers=self.state["group_x_admin"].auth.header,
            params=request_body,
            status=status
        )

    def step_3j(self, status:int=204):
        """admin: make user_a group & site admin"""

        request_body = {
            "siteAdmin": True,
            "groupAdmin": True
        }

        response = self.testapp.put_json(
            base_url + "/users/" + self.state["user_a"].uuid,
            headers=self.state["admin"].auth.header,
            params=request_body,
            status=status
        )

    def step_3k(self, status:int=200):
        """Check if the previous admin status change worked"""

        response = self.testapp.get(
            "/api/admin",
            headers=self.state["admin"].auth.header,
            status=status
        )

        if status==200: # check, if the admin status change worked

            for user in response.json["users"]:
                if user["id"]["uuid"] == self.state["user_a"].uuid:
                    assert user["group_admin"] == True, (
                        "The group_admin status change of user_a did not work."
                    )
                    assert user["site_admin"] == True, (
                        "The site_admin status change of user_a did not work."
                    )

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


    def test_steps(self):
        # set initial state:
        self.state = {
            "user_a": self.users["user_a"],
            "user_b": self.users["user_b"],
            "user_c": self.users["user_c"],
            "group_x_admin": self.users["group_x_admin"],
            "group_y_admin": self.users["group_y_admin"],
            "admin": self.users["admin"],
            "apikey_label": "test_key",
            "apikey_response_a": None, # slot to store the apikey response for user_a
            "apikey_response_x": None, # slot to store the apikey response for group_x_admin
            "apikey_response_admin": None, # slot to store the apikey response for admin
            "user_name_change_to": None, # slot to store the last user name change
            "groups": None # slot to store all group information
        }

        # execute all test steps
        self._test_all_steps()