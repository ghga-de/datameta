import unittest

from pyramid import testing
from pyramid.httpexceptions import HTTPFound
import pytest
import transaction
from datameta import scripts, models, security


def dummy_request(dbsession):
    return testing.DummyRequest(dbsession=dbsession)


class BaseIntegrationTest(unittest.TestCase):
    def setUp(self):
        """Setup Test Server"""
        from datameta import main
        settings = {
            'datameta.site_id_prefix.users': "DMU-",
            'datameta.site_id_prefix.groups': "DMG-",
            'datameta.site_id_prefix.submissions': "DMS-",
            'datameta.site_id_prefix.metadatasets': "DMR-",
            'datameta.site_id_prefix.files': "DMF-",
            'datameta.site_id_digits.users': 8,    
            'datameta.site_id_digits.groups': 8,    
            'datameta.site_id_digits.submissions': 8,    
            'datameta.site_id_digits.metadatasets': 8,   
            'datameta.site_id_digits.files': 8,      
            'datameta.smtp_host': "localhost",      
            'datameta.smtp_port': "587",      
            'datameta.smtp_user': "",      
            'datameta.smtp_pass': "",      
            'datameta.smtp_tls': "",       
            'datameta.smtp_from': "",       
            'datameta.apikeys.max_expiration_period': 30,
            
            'pyramid.reload_templates': True,
            'pyramid.debug_authorization': False,
            'pyramid.debug_notfound': False,
            'pyramid.debug_routematch': False,
            'pyramid.default_locale_name': "en",
            'pyramid.includes': "pyramid_debugtoolbar",
                
            #'sqlalchemy.url': 'sqlite:///:memory:',
            'sqlalchemy.url': 'postgresql://datameta:datameta@datameta-postgresql/datameta',
            'sqlalchemy.isolation_level': "SERIALIZABLE",

            'session.type': "ext:memcached",
            'session.url': "datameta-memcached:11211",
            'session.key': "datameta",
            'session.secret': "test",
            'session.cookie_on_exception': False,

            'retry.attempts': 10,
        }
        app = main({}, **settings)
        from webtest import TestApp
        self.testapp = TestApp(app)

        # init database:
        from datameta.models import (
            get_engine,
            get_session_factory,
            get_tm_session,
        )

        self.engine = get_engine(settings)
        
        from datameta.models.meta import Base
        Base.metadata.create_all(self.engine)

        session_factory = get_session_factory(self.engine)

        # populate db:
        with transaction.manager:
            temp_session = get_tm_session(session_factory, transaction.manager)

            email = "admin@admin.admin"
            password = "admin"
            fullname = "admin"
            groupname = "admin"

            init_group = models.Group(
                id=0,
                name=groupname,
                site_id="init_test_user_id"
            )
            root = models.User(
                id=0,
                site_id="init_test_user_id",
                enabled=True,
                email=email,
                pwhash=security.hash_password(password),
                fullname=fullname,
                group=init_group,
                group_admin=True,
                site_admin=True
            )
            temp_session.add(root)

        self.session = get_tm_session(session_factory, transaction.manager)
        
    def tearDown(self):
        """Teardown Test Server"""
        from datameta.models.meta import Base
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