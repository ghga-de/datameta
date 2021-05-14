import os
import json
from dataclasses import dataclass, field
import hashlib
from typing import Optional, List

from datameta.models.db import DateTimeMode, File

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
class AuthFixture():
    """A container for token auth information"""
    apikey:Optional[str] = None
    apikey_id:Optional[str] = None
    header:dict = field(default_factory=dict)

    def __post_init__(self):
        self.header = {
            "Authorization": f"Bearer {self.apikey}"
        }


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
    site_read:bool
    enabled:bool
    # will be set once added to db:
    auth: AuthFixture = AuthFixture()
    expired_auth: AuthFixture = AuthFixture()
    uuid:Optional[str] = None 
    group_site_id:Optional[str] = None 
    group_uuid_id:Optional[str] = None

default_users_json = os.path.join(base_dir, "default_users.json")
with open(default_users_json, "r") as json_:
    default_users = {
        user["site_id"]: UserFixture(**user)
        for user in json.load(json_)
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


# read in default metadatasets:
@dataclass
class MetaDataSetFixture():
    """A container for Metadatasets."""
    site_id: str
    user: str
    record: dict
    uuid: Optional[str] = None 
    submitted:bool = False


default_metadatasets_json = os.path.join(base_dir, "default_metadatasets.json")
with open(default_metadatasets_json, "r") as json_:
    default_metadatasets = {
        mset["site_id"]: MetaDataSetFixture(**mset)
        for mset in json.load(json_)
    }


# read test files:
# Test files will not be added to the database by default
def calc_checksum(file_path:str):
    with open(file_path, "rb") as file_:
        byte_content = file_.read()
        return hashlib.md5(byte_content).hexdigest()

class FileFixture():
    """Container for File fixtures"""
    def __init__(self, name, site_id=None, user=None, submitted=False):
        self.name = name

        # set path:
        self.path = os.path.join(base_dir, name)
        
        # set content: 
        with open(self.path, "r") as test_file:
            self.content = test_file.read()
        
        # set md5 sum
        self.checksum = calc_checksum(self.path)

        # additional parameters for default files:
        self.site_id = site_id
        self.user = user
        self.uuid = None # will be set once added to the database 
        self.submitted = submitted

test_files = [
    FileFixture(name) 
    for name in os.listdir(base_dir)
    if "test_file_" in name
]


# read default files:
# Default files will be added to the database
default_files_json = os.path.join(base_dir, "default_files.json")
with open(default_files_json, "r") as json_:
    default_files = {
        file["site_id"]: FileFixture(**file)
        for file in json.load(json_)
    }


# read in default submissions:
@dataclass
class SubmissionFixture():
    """A container for Submissions."""
    site_id: str
    label: str
    date: str
    group: str
    metadataset_ids: List[str]
    files: Optional[List[str]] = None
    uuid: Optional[str] = None

default_submissions_json = os.path.join(base_dir, "default_submissions.json")
with open(default_submissions_json, "r") as json_:
    default_submissions = {
        sub["site_id"]: SubmissionFixture(**sub)
        for sub in json.load(json_)
    }