# Copyright 2021 Universität Tübingen, DKFZ and EMBL for the German Human Genome-Phenome Archive (GHGA)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Testing user management via API request
"""
from parameterized import parameterized

from sqlalchemy.orm import joinedload

from . import BaseIntegrationTest
from datameta import models
from datameta.api import base_url
import re

class TestUserManagement(BaseIntegrationTest):

    def do_request(self, user_uuid, **params):
        response = self.testapp.put_json(
            f"{base_url}/users/{user_uuid}",
            **params
        )
        return response

    def process_name_change_request(self, testname, user, target_user, new_name, expected_response):
        response = self.do_request(
                user_uuid   = target_user.uuid,
                status      = expected_response,
                headers     = self.apikey_auth(user),
                params      = {"name": new_name}
                )

        db_user = self.fixture_manager.get_fixture_db('users', target_user.site_id)
        expected_outcome = any([
            expected_response == 204 and db_user.fullname == new_name,
            expected_response == 403 and db_user.fullname == target_user.fullname
        ])
        
        assert expected_outcome, f"{testname} failed"

    def process_group_change_request(self, testname, user, target_user, new_group_uuid, expected_response):
        response = self.do_request(
                target_user.uuid,
                status=expected_response,
                headers=self.apikey_auth(user),
                params={"groupId": str(new_group_uuid)}
                )

        db_user = self.fixture_manager.get_fixture_db('users', target_user.site_id, joinedload(models.User.group))

        if expected_response == 204:
            assert db_user.group.uuid == new_group_uuid
        elif expected_response == 403:
            assert db_user.group.uuid != new_group_uuid

    def process_status_change_request(self, testname, user, target_user, actions, expected_response, revert=False):
        camel_to_snake = lambda name : re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()

        # Build the request parameters
        params = dict()
        for action in actions:
            value = (action[0] == "+") if not revert else (action[0] != "+")
            params[action[1:]] = value

        # Make the PUT request and store the state of the user before and after the request
        db_user_before   = self.fixture_manager.get_fixture_db('users', target_user.site_id)
        response         = self.do_request(target_user.uuid, status=expected_response, headers=self.apikey_auth(user), params=params)
        db_user_after    = self.fixture_manager.get_fixture_db('users', target_user.site_id)

        # Check if changes were made if expected
        if expected_response == 204:
            for attr_name, value in params.items():
                attr_name = camel_to_snake(attr_name)
                assert getattr(db_user_after, attr_name) == value, f"The field '{attr_name}' was not changed as expected"

        # Check if state persisted if expected
        if expected_response != 204:
            for attr_name, value in params.items():
                attr_name = camel_to_snake(attr_name)
                assert getattr(db_user_after, attr_name) == getattr(db_user_before, attr_name), f"The field '{attr_name}' was changed unexpectedly!"


    def setUp(self):
        super().setUp()
        self.fixture_manager.load_fixtureset('groups')
        self.fixture_manager.load_fixtureset('users')
        self.fixture_manager.load_fixtureset('apikeys')

    @parameterized.expand([
        #TEST_NAME                                  , EXECUTING_USER    , TARGET_USER   , NEW_NAME                     , EXP_RESPONSE
        ("self_name_change"                         , "user_a"          , "user_a"      , "changed_by_user_a"          , 204), 
        ("other_name_change_by_regular_user"        , "user_a"          , "user_c"      , "changed_by_user_a"          , 403), 
        ("other_name_change_by_own_group_admin"     , "group_x_admin"   , "user_a"      , "changed_by_group_x_admin"   , 204), 
        ("other_name_change_by_other_group_admin"   , "group_x_admin"   , "user_c"      , "changed_by_group_x_admin"   , 403), 
        ("other_name_change_by_admin"               , "admin"           , "user_a"      , "changed_by_admin"           , 204), 
    ])
    def test_name_change(self, testname:str, executing_user:str, target_user:str, new_name:str, expected_response:int):
        user          = self.fixture_manager.get_fixture('users', executing_user)
        target_user   = self.fixture_manager.get_fixture('users', target_user)

        self.process_name_change_request(testname, user, target_user, new_name, expected_response)

    @parameterized.expand([
        # TEST_NAME                                  , EXECUTING USER    , TARGET_USER       , NEW_GROUP   , EXP_RESPONSE
        ("self_group_change"                         , "user_a"          , "user_a"          , "group_y"   , 403), 
        ("self_group_change_by_group_admin"          , "group_x_admin"   , "group_x_admin"   , "group_y"   , 403), 
        ("other_group_change_by_group_admin"         , "group_x_admin"   , "user_a"          , "group_y"   , 403), 
        ("other_group_change_by_other_group_admin"   , "group_x_admin"   , "user_c"          , "group_x"   , 403), 
        ("self_group_change_by_admin"                , "admin"           , "admin"           , "group_y"   , 204), 
        ("other_group_change_by_admin"               , "admin"           , "user_a"          , "group_y"   , 204), 
    ])
    def test_group_change(self, testname:str, executing_user:str, target_user_name:str, new_group:str, expected_response:int):
        user                 = self.fixture_manager.get_fixture('users', executing_user)
        target_user          = self.fixture_manager.get_fixture('users', target_user_name)
        new_group_uuid       = self.fixture_manager.get_fixture('groups', new_group).uuid
        current_group_uuid   = self.fixture_manager.get_fixture('groups', target_user.group).uuid

        self.process_group_change_request(testname, user, target_user, new_group_uuid, expected_response)

        if expected_response == 204:
            self.process_group_change_request(testname, user, target_user, current_group_uuid, expected_response)
        
    @parameterized.expand([
        # TEST_NAME                                            EXECUTING_USER      TARGET_USER         CHANGES                           EXP_RESPONSE 
        ("self_regular_user_grant_site_admin"                , "user_a"          , "user_a"          , ("+siteAdmin", )                , 403), 
        ("other_regular_user_revoke_site_admin_from_admin"   , "user_a"          , "admin"           , ("-siteAdmin", )                , 403), 
        ("other_group_admin_grant_group_admin_to_regular"    , "group_x_admin"   , "user_a"          , ("+groupAdmin", )               , 204), 
        ("self_group_admin_grant_site_admin"                 , "group_x_admin"   , "group_x_admin"   , ("+siteAdmin", )                , 403), 
        ("other_group_admin_grant_site_admin_to_regular"     , "group_x_admin"   , "user_a"          , ("+siteAdmin", )                , 403), 
        ("other_group_admin_revoke_site_admin_from_admin"    , "group_x_admin"   , "admin"           , ("-siteAdmin", )                , 403), 
        ("other_site_admin_grant_admins_to_regular"          , "admin"           , "user_a"          , ("+siteAdmin", "+groupAdmin")   , 204), 
        ("self_disable_regular_user"                         , "user_a"          , "user_a"          , ("-enabled", )                  , 403), 
        ("self_enable_regular_user"                          , "user_a"          , "user_a"          , ("+enabled", )                  , 403), 
        ("other_disable_regular_user"                        , "group_x_admin"   , "user_a"          , ("-enabled", )                  , 204), 
        ("other_disable_regular_user_other_group"            , "group_x_admin"   , "user_c"          , ("-enabled", )                  , 403), 
        ("self_regular_user_grant_site_read"                 , "user_a"          , "user_a"          , ("+siteRead", )                 , 403), 
        ("other_group_admin_grant_site_read_to_regular"      , "group_x_admin"   , "user_a"          , ("+siteRead", )                 , 403), 
        ("other_site_admin_grant_site_read_to_regular"       , "admin"           , "user_a"          , ("+siteRead", )                 , 204), 
    ])
    def test_status_changes(self, testname:str, executing_user:str, target_user:str, actions:tuple, expected_response:int):
        user = self.fixture_manager.get_fixture('users', executing_user)
        target_user = self.fixture_manager.get_fixture('users', target_user)

        self.process_status_change_request(testname, user, target_user, actions, expected_response)
        if expected_response == 204:
            self.process_status_change_request(testname, user, target_user, actions, expected_response, revert=True)
        

    def test_edgecase_status_changes(self):
        admin           = self.fixture_manager.get_fixture('users', 'admin')
        user_b          = self.fixture_manager.get_fixture('users', 'user_b')
        group_x_admin   = self.fixture_manager.get_fixture('users', 'group_x_admin')

        # admin: make user_b a site_admin
        self.do_request(user_b.uuid, status=204, headers=self.apikey_auth(admin), params={"siteAdmin": True})

        # group_x_admin: disable user_b which is a site_admin
        self.do_request(user_b.uuid, status=403, headers=self.apikey_auth(group_x_admin), params={"enabled": False})

        # admin: re-enable user_b which is a site_admin
        self.do_request(user_b.uuid, status=204, headers=self.apikey_auth(admin), params={"enabled": True})
