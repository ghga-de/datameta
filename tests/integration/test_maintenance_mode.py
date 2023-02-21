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

import os
from parameterized import parameterized

from . import BaseIntegrationTest
from datameta.api import base_url


class TestMaintenanceMode(BaseIntegrationTest):
    """Test if application reactes correctly to existance of maintenance mode file"""

    def setUp(self):
        super().setUp()
        self.settings["datameta.maintenance_mode.exclude_request_paths"] = ["/login", base_url + "/metadata"]
        self.maintenance_mode_file = self.settings["datameta.maintenance_mode.path"]

    def ensure_exists_maintenance_mode_file(self):
        with open(self.maintenance_mode_file, 'a'):
            os.utime(self.maintenance_mode_file, None)

    def ensure_exists_not_maintenance_mode_file(self):
        if os.path.exists(self.maintenance_mode_file):
            os.remove(self.maintenance_mode_file)

    @parameterized.expand([
        # test_name route expected_response_exists expected_response_not_exists
        ("Normal view", "/", 302, 503),
        ("Excluded view", "/login", 200, 200),
        ("Normal view", "/register", 200, 503),
        ("Normal api", "/api", 302, 503),
        ("Normal api", base_url + "/server", 500, 503),
        ("Normal api", base_url + "/rpc/whoami", 401, 503),
        ("Excluded api", base_url + "/metadata", 401, 401),
        ("Normal api", base_url + "/files", 404, 503),
        ])
    def test_maintenance_mode(self, _, route: str, expected_response: int, expected_response_not_exists: int):
        """Test that the maintenance mode is working as expected"""
        self.ensure_exists_maintenance_mode_file()
        self.testapp.get(route, status=expected_response)
        self.ensure_exists_not_maintenance_mode_file()
        self.testapp.get(route, status=expected_response_not_exists)
        self.ensure_exists_maintenance_mode_file()
        self.testapp.get(route, status=expected_response)
