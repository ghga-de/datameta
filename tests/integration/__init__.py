"""The skeleton of the test framework.
"""

import os
import json

import unittest
from webtest import TestApp
import tempfile

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

from .fixtures import (
    db_url,
    memcached_url, 
    FixtureManager,
    default_settings,
    holders
)

from .utils import get_auth_header

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
    def setUp(self):
        """Setup Test Server"""
        self.settings = default_settings
        
        # setup temporary storage location:
        self.storage_path_obj = tempfile.TemporaryDirectory()
        self.storage_path = self.storage_path_obj.name
        self.settings["datameta.storage_path"] = self.storage_path

        # initialize DB 
        self.initDb()
        
        # Create fixture manager
        self.fixture_manager = FixtureManager(self.session_factory, self.storage_path)

        from datameta import main
        app = main({}, **self.settings)
        self.testapp = TestApp(app)
        
    def tearDown(self):
        """Teardown Test Server"""
        transaction.abort()
        Base.metadata.drop_all(self.engine)
        del self.testapp
        self.storage_path_obj.cleanup()

    def apikey_auth(self, user:holders.UserFixture) -> dict:
        apikey = self.fixture_manager.get_fixture('apikeys', user.site_id)
        return get_auth_header(apikey.value_plain)

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
