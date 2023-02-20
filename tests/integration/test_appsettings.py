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

from parameterized import parameterized
from datameta.api import base_url
from . import BaseIntegrationTest


class TestAppSettings(BaseIntegrationTest):
    '''
    Tests for get and set requests to the endpoint 'appsettings'.
    '''

    def setUp(self):
        super().setUp()
        self.fixture_manager.load_fixtureset('groups')
        self.fixture_manager.load_fixtureset('users')
        self.fixture_manager.load_fixtureset('apikeys')
        self.fixture_manager.load_fixtureset('appsettings')

    @parameterized.expand([
        ("unauthorized_no_user", "", 401),
        ("forbidden_group_admin", "group_x_admin", 403),
        ("forbidden_user_site_read", "user_site_read", 403),
        ("ok_admin", "admin", 200)
        ])
    def test_get_appsettings(self, testname: str, executing_user: str, expected_status: int):
        '''
        Test concept:
                - authorization for get requests to endpoint 'appsettings'
        '''
        user = self.fixture_manager.get_fixture('users', executing_user) if executing_user else None
        auth_headers = self.apikey_auth(user) if user else {}

        self.testapp.get(
            f"{base_url}/appsettings",
            headers = auth_headers,
            status = expected_status
        )

    @parameterized.expand([
        # TEST_NAME, EXEC_USER, RESPONSE, NEW_VALUE, NEW_VALUE_TYPE, IS_UPDATED
        # authorization errors
        ("unauthorized_no_user", "", 401, "5", "int", False),
        ("forbidden_no_admin", "user_a", 403, "5", "int", False),
        # validation errors
        ("wrong_type_int", "admin", 400, "no int", "int", False),
        ("wrong_type_float", "admin", 400, "no float", "float", False),
        ("wrong_type_date", "admin", 400, "no date", "date", False),
        ("wrong_type_time", "admin", 400, "no time", "time", False),
        # empty and nullables
        ("wrong_none", "admin", 400, None, "string", False),
        ("updated_empty", "admin", 204, "", "string", True),
        # successful requests
        ("updated_string", "admin", 204, "i am a string", "string", True),
        ("updated_int", "admin", 204, "1", "int", True),
        ("updated_float", "admin", 204, "1.1", "float", True),
        ("updated_date", "admin", 204, "2022-01-01", "date", True),
        ("updated_time", "admin", 204, "01:01:01", "time", True),
        ])
    def test_put_appsettings(self,
                        testname: str,
                        executing_user: str,
                        expected_status: int,
                        new_value: str,
                        new_value_type: str,
                        is_updated: bool
                        ):
        '''
        Test concept:
                - get all appsettings from the endpoint
                    - only existing appsettings are used
                    - requires that it exists at least one updatable setting for all types
                - put new value to the endpoint
                    - endpoint requires { "value": "string" }
                    - update only possible if the types are suitable
                - get again appsettings from the endpoint
                    - if the request was expected to be successful ('is_updated'), value should be new_value, else the old
                - response '404 Setting does not exist' is not tested here
        '''
        def to_uuid_dict(iterable_container):
            '''
            Returns a dictionary of dictionaries indexable by the 'uuid'.

                    Parameters:
                        iterable_container (Iterable): an iterable container containing
                                       dictionaries (requires entry: 'id' : {'uuid' : _ })

                    Returns:
                        (Iterable): a dictionary of dictionaries indexable by the 'uuid'
            '''
            return { str( e['id']['uuid']) : e for e in iterable_container }

        user = self.fixture_manager.get_fixture('users', executing_user) if executing_user else None
        auth_headers = self.apikey_auth(user) if user else {}

        # administrative rights necessary to get appsettings from endpoint
        admin = self.fixture_manager.get_fixture('users', 'admin')
        auth_headers_admin = self.apikey_auth(admin)

        # get all appsettings from endpoint (necessary to get the uuids of the entries)
        app_settings = self.testapp.get(
            f"{base_url}/appsettings",
            headers = auth_headers_admin
        )

        # transform to dictionary with the returned appsettings indexable by the uuid
        app_settings = to_uuid_dict(app_settings.json)

        # perform put request for all settings with suitable types
        for uuid, setting in app_settings.items():
            if new_value_type == setting['valueType']:
                self.testapp.put_json(
                    f"{base_url}/appsettings/{uuid}",
                    headers = auth_headers,
                    params = { "value": new_value },
                    status = expected_status
                    )

        # get again appsettings from endpoint with administrative rights
        app_settings_updated = self.testapp.get(
            f"{base_url}/appsettings",
            headers = auth_headers_admin
            )
        app_settings_updated = to_uuid_dict(app_settings_updated.json)

        # iterate through appsettings after put was requested
        # if passed 'value_type' was equal to the type in the database and
        # the request was expected to be successful ('is_updated') the value
        # should be the new value else the old
        for uuid, setting in app_settings_updated.items():
            if new_value_type == setting['valueType']:
                if is_updated:
                    assert app_settings_updated[uuid]['value'] == new_value
                else:
                    assert app_settings_updated[uuid]['value'] == app_settings[uuid]['value']
