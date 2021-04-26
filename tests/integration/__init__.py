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

from .utils import create_file, create_metadataset, create_user, create_metadatum, set_application_settings
from .fixtures import (
    db_url, 
    memcached_url, 
    default_settings,
    default_users,
    default_metadata,
    metadata_records,
    test_files,
    default_files,
    default_metadatasets,
    default_submissions
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
            site_id: create_user(self.session_factory, user)
            for site_id, user in default_users.items()
        }

        # create default metadata:
        self.metadata = {
            name: create_metadatum(self.session_factory, mdatum)
            for name, mdatum in default_metadata.items()
        }

        # add default metadatasets to the database:
        self.default_metadatasets = {
            site_id: create_metadataset(self.session_factory, metadataset)
            for site_id, metadataset in default_metadatasets.items()
        }

        # add default files to the database:
        self.default_files = {
            site_id: create_file(self.session_factory, self.storage_path, file)
            for site_id, file in default_files.items()
        }

        # add application settings:
        set_application_settings(self.session_factory)

    def setUp(self):
        """Setup Test Server"""
        self.settings = default_settings
        
        # setup temporary storage location:
        self.storage_path_obj = tempfile.TemporaryDirectory()
        self.storage_path = self.storage_path_obj.name
        self.settings["datameta.storage_path"] = self.storage_path

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
        self.storage_path_obj.cleanup()

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