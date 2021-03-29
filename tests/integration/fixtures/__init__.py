import os
import json
from dataclasses import dataclass
import hashlib
from typing import Optional, Union

from datameta.models.db import DateTimeMode

# get URL to test db from environment variable:
db_url = os.getenv("SQLALCHEMY_TEST_URL")
assert db_url, "Could not find environment variable \"SQLALCHEMY_TEST_URL\""
memcached_url = os.getenv("SESSION_URL")
assert memcached_url, "Could not find environment variable \"SESSION_URL\""

# read settings.json
base_dir = os.path.dirname(__file__)
default_settings_json = os.path.join(base_dir, "settings.json")
with open(default_settings_json, "r") as json_:
    default_settings = json.load(json_)
default_settings["sqlalchemy.url"] = db_url
default_settings["session.url"] = memcached_url

# read default user.json:
@dataclass
class UserFixture():
    """A container for user information"""
    email:str
    password:str 
    fullname:str
    site_id:str
    groupname:str
    group_admin:bool
    site_admin:bool
    # will be set once added to db:
    token: Optional[str] = None
    expired_token: Optional[str] = None
    uuid:Optional[str] = None 

default_users_json = os.path.join(base_dir, "default_users.json")
with open(default_users_json, "r") as json_:
    default_users = {
        name: UserFixture(**user)
        for name, user in json.load(json_).items()
    }

# read default metadatum.json:
@dataclass
class MetaDatumFixture():
    """A container for metadatum information"""
    name: str
    mandatory: bool
    order: int
    isfile: bool
    site_unique: bool
    submission_unique: bool
    datetimefmt: Optional[str] = None
    _datetimemode: Optional[str] = None
    datetimemode: Optional[DateTimeMode] = None
    regexp: Optional[str] = None
    example: Optional[str] = None
    short_description: Optional[str] = None
    long_description: Optional[str] = None
    uuid: Optional[str] = None

    def __post_init(self):
        if self._datetimemode:
            self.datetimemode = getattr(DateTimeMode, self._datetimemode)

default_metadata_json = os.path.join(base_dir, "default_metadata.json")
with open(default_metadata_json, "r") as json_:
    default_metadata = {
        mdatum["name"]: MetaDatumFixture(**mdatum)
        for mdatum in json.load(json_)
    }

# read metadata_records.json:
metadata_records_json = os.path.join(base_dir, "metadata_records.json")
with open(metadata_records_json, "r") as json_:
    metadata_records = json.load(json_)

# read test files:
class FileFixture():
    """Container for File fixtures"""
    def __init__(self, name):
        self.name = name

        # set path:
        self.path = os.path.join(base_dir, name)
        
        # set content: 
        with open(self.path, "r") as test_file:
            self.content = test_file.read()
        
        # set md5 sum
        with open(self.path, "rb") as test_file:
            byte_content = test_file.read()
            self.md5 = hashlib.md5(byte_content).hexdigest()


test_files = [
    FileFixture(name) 
    for name in os.listdir(base_dir)
    if "test_file_" in name
]