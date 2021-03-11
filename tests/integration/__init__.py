from typing import Optional
import unittest

from pyramid import testing
from pyramid.httpexceptions import HTTPFound
import pytest
import transaction
from sqlalchemy_utils import create_database, drop_database, database_exists
import os
import json
from datameta import scripts, models, security
from datameta.models import (
    get_engine,
    get_session_factory,
    get_tm_session,
)
from datameta.models.meta import Base
from webtest import TestApp
from dataclasses import dataclass
from copy import deepcopy

# get URL to test db from environment variable:
db_url = os.getenv("SQLALCHEMY_TEST_URL")
assert db_url, "Could not find environment variable \"SQLALCHEMY_TEST_URL\""

# read settings.json
default_settings_json = os.path.join(
    os.path.dirname(__file__), 
    "fixtures", 
    "settings.json"
)
with open(default_settings_json, "r") as json_:
    default_settings = json.load(json_)
default_settings["sqlalchemy.url"] = db_url

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
    uuid:Optional[str] = None # will be set once
                              # added to the DB

default_users_json = os.path.join(
    os.path.dirname(__file__), 
    "fixtures", 
    "default_users.json"
)
with open(default_users_json, "r") as json_:
    default_users = {
        name: UserFixture(**user)
        for name, user in json.load(json_).items()
    }


def create_user(
    session_factory,
    user:UserFixture 
):
    """Add a datameta user to the database"""
    with transaction.manager:
        session = get_tm_session(session_factory, transaction.manager)
        
        # check if group exists otherwise create it:
        group_obj = session.query(models.Group).filter(models.Group.name==user.groupname).one_or_none()
        if not group_obj:
            group_obj = models.Group(
                name=user.groupname,
                site_id=f"{user.groupname}_id" # ingore usual site id format
            )
            session.add(group_obj)
            session.flush()
        
        # create user:
        user_obj = models.User(
            site_id=user.site_id, # ingore usual site id format
            enabled=True,
            email=user.email,
            pwhash=security.hash_password(user.password),
            fullname=user.fullname,
            group=group_obj,
            group_admin=user.group_admin,
            site_admin=user.site_admin
        )
        session.add(user_obj)
        session.flush()

        # return user updated with uuid:
        user_updated = deepcopy(user)
        user_updated.uuid = str(user_obj.uuid)
        return user_updated

class BaseIntegrationTest(unittest.TestCase):
    """Base TestCase to inherit from"""

    state:dict # this slot can be used to store
               # state when a test is broken down
               # into multiple functions (steps),
               # moreover, any initial parameters/fixtures
               # should be defined here at the beginning
               # of each test

    def initDb(self):
        # create database from scratch:
        if database_exists(db_url):
            drop_database(db_url)
        create_database(db_url)

        # get engine and session factory
        self.engine = get_engine(self.settings)
        self.session_factory = get_session_factory(self.engine)

        # create models:
        Base.metadata.create_all(self.engine)
        
        # create default users:
        self.users = {
            name: create_user(self.session_factory, user)
            for name, user in default_users.items()
        }

    def setUp(self):
        """Setup Test Server"""
        self.settings = default_settings
        
        self.initDb()

        from datameta import main
        app = main({}, **self.settings)
        self.testapp = TestApp(app)
        
    def tearDown(self):
        """Teardown Test Server"""
        transaction.abort()
        Base.metadata.drop_all(self.engine)
        del self.testapp

    def _steps(self):
        """
        If a class inheriting from this class defines methods named according to the
        pattern \"step_<no.>_<titel>\", this function can be called to iterate over
        them in the correct order.
        """
        for name in sorted(dir(self)):
            if name.startswith("step"):
                yield name, getattr(self, name) 

    def _test_all_steps(self):
        """
        Can be called to test all steps in alphanumerical order
        """
        for name, step in self._steps():
            step()