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
from .utils import get_auth_headers

from datameta import models
from datameta.api import base_url

class TestUserManagement(BaseIntegrationTest):

    def step_1(self, status:int=200):
        """user_a: change name of user_a"""
        request_body = {
            "email": self.state["user_a"].email,
            "password": self.state["user_a"].password,
            "name": "changed_by_user_a"
        }

        response = self.testapp.put_json(
            base_url + "/user",
            params=request_body,
            status=status
        )

    def step_2(self, status:int=403):
        """user_a: change name of user_c"""
        request_body = {
            "email": self.state["user_a"].email,
            "password": self.state["user_a"].password,
            "name": "changed_by_user_a"
        }

        response = self.testapp.put_json(
            base_url + "/user/" + self.state["user_c"].uuid,
            params=request_body,
            status=status
        )

    def step_3(self, status:int=200):
        """group_x_admin: change name of user_a"""
        request_body = {
            "email": self.state["group_x_admin"].email,
            "password": self.state["group_x_admin"].password,
            "name": "changed_by_group_x_admin"
        }

        response = self.testapp.put_json(
            base_url + "/user/" + self.state["user_a"].uuid,
            params=request_body,
            status=status
        )

    def step_4(self, status:int=403):
        """group_x_admin: change name of user_c"""
        request_body = {
            "email": self.state["group_x_admin"].email,
            "password": self.state["group_x_admin"].password,
            "name": "changed_by_group_x_admin"
        }

        response = self.testapp.put_json(
            base_url + "/user/" + self.state["user_c"].uuid,
            params=request_body,
            status=status
        )

    def step_5(self, status:int=200):
        """admin: change name of user_a"""
        request_body = {
            "email": self.state["admin"].email,
            "password": self.state["admin"].password,
            "name": "changed_by_admin"
        }

        response = self.testapp.put_json(
            base_url + "/user/" + self.state["user_a"].uuid,
            params=request_body,
            status=status
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
        }

        # execute all test steps
        self._test_all_steps()