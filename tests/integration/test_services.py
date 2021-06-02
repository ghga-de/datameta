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

"""Testing Settings via API request
"""
from parameterized import parameterized
from datameta.api import base_url
from . import BaseIntegrationTest

# One Service already in Database
# Two Users already in Database: User 1 is site_admin, User is not
# Try every (200) also as a not authorized user

# POST Service
# Create a new Service (200), Check Response
# Try to create a service with the same name (400)

# GET Services
# Run a get (200), check if everything okay

# PUT Service
# Set user 1 (200), Check Response
# Set user 2 (200), Check Response
# Change Name of Service 2 to Service 1 (400)
# Change something on a Service, that does not exist (404)





