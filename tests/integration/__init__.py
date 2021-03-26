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

from .utils import create_user, create_metadatum
from .fixtures import (
    db_url, 
    memcached_url, 
    default_settings,
    default_users,
    default_metadata,
    metadata_records,
    test_files
)

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

        # create default metadata:
        self.metadata = {
            name: create_metadatum(self.session_factory, mdatum)
            for name, mdatum in default_metadata.items()
        }

    def setUp(self):
        """Setup Test Server"""
        self.settings = default_settings
        
        # initialize DB and provide metadata and file fixtures
        self.initDb()
        self.metadata_records = metadata_records
        self.test_files = test_files

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