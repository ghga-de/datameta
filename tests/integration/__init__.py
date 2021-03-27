"""The skeleton of the test framework.
"""

import os
import json

import unittest
from webtest import TestApp
import pytest

from pyramid import testing
from pyramid.httpexceptions import HTTPFound
import transaction
from sqlalchemy_utils import create_database, drop_database, database_exists

from datameta import models
from datameta.models import (
    get_engine,
    get_session_factory
)
from datameta.models.meta import Base

from .utils import UserFixture, create_user

# get URL to test db from environment variable:
db_url = os.getenv("SQLALCHEMY_TEST_URL")
assert db_url, "Could not find environment variable \"SQLALCHEMY_TEST_URL\""
memcached_url = os.getenv("SESSION_URL")
assert memcached_url, "Could not find environment variable \"SESSION_URL\""

# read settings.json
default_settings_json = os.path.join(
    os.path.dirname(__file__), 
    "fixtures", 
    "settings.json"
)
with open(default_settings_json, "r") as json_:
    default_settings = json.load(json_)
default_settings["sqlalchemy.url"] = db_url
default_settings["session.url"] = memcached_url

# read default user.json:
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


class BaseIntegrationTest(unittest.TestCase):
    """Base TestCase to inherit from"""

    state:dict # this slot can be used to store
               # state when a test is broken down
               # into multiple functions (steps),
               # moreover, any initial parameters/fixtures
               # should be defined here at the beginning
               # of each test

    def get_api_key(self, user_id, base_url, expires=None):
        user = self.users[user_id]
        request_body = {
            "email": user.email, "password": user.password, "label": "test_key"
        }
        if expires:
            request_body["expires"] = expires

        response = self.testapp.post_json(
            base_url + "/keys", params=request_body, status=200
        )
        return response.json["token"]

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