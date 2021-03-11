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
default_users_json = os.path.join(
    os.path.dirname(__file__), 
    "fixtures", 
    "default_users.json"
)
with open(default_users_json, "r") as json_:
    default_users = json.load(json_)


def create_user(
    session_factory, 
    email:str, 
    password:str, 
    fullname:str, 
    site_id:str,
    groupname:str,
    group_admin:bool,
    site_admin:bool
):
    """Add a datameta user to the database"""
    with transaction.manager:
        session = get_tm_session(session_factory, transaction.manager)
        
        # check if group exists otherwise create it:
        group = session.query(models.Group).filter(models.Group.name==groupname).one_or_none()
        if not group:
            group = models.Group(
                name=groupname,
                site_id=f"{groupname}_id" # ingore usual site id format
            )
            session.add(group)
            session.flush()
        
        # create user:
        user = models.User(
            site_id=site_id, # ingore usual site id format
            enabled=True,
            email=email,
            pwhash=security.hash_password(password),
            fullname=fullname,
            group=group,
            group_admin=group_admin,
            site_admin=site_admin
        )
        session.add(user)
        session.flush()

        return user

class BaseIntegrationTest(unittest.TestCase):
    """Base TestCase to inherit from"""

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
            name: create_user(self.session_factory, **user)
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