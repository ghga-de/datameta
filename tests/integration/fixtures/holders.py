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

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Entity:
    __db_class__   : str
    id             : int
    uuid           : str


@dataclass
class GroupFixture(Entity):
    name      : str
    site_id   : str


@dataclass
class UserFixture(Entity):
    email         : str
    pwhash        : str
    password      : str
    fullname      : str
    site_id       : str
    group         : str
    group_admin   : bool
    site_admin    : bool
    site_read     : bool
    enabled       : bool


@dataclass
class ApiKeyFixture(Entity):
    label         : str
    expires       : datetime
    value         : str
    value_plain   : str
    user          : str


@dataclass
class PasswordTokenFixture(Entity):
    value_plain   : str
    value         : str
    user          : str
    expires       : datetime


@dataclass
class MetaDataSetFixture(Entity):
    site_id      : str
    user         : str
    records      : Optional[dict] = None
    submission   : Optional[str]  = None


@dataclass
class MetaDatumFixture(Entity):
    name                : str
    mandatory           : bool
    example             : str
    order               : int
    isfile              : bool
    submission_unique   : bool
    site_unique         : bool
    datetimefmt         : Optional[str] = None
    service             : Optional[dict] = None


@dataclass
class FileFixture(Entity):
    site_id            : str
    name               : str
    user               : dict
    content_uploaded   : bool
    checksum           : str


@dataclass
class SubmissionFixture(Entity):
    site_id   : str
    label     : str
    date      : datetime
    group     : dict


@dataclass
class ServiceFixture(Entity):
    site_id   : str
    name      : str
    users     : list


@dataclass
class ServiceExecutionFixture(Entity):
    service       : dict
    user          : dict
    metadataset   : dict
    datetime      : datetime
