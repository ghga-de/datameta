import argparse
import sys

from pyramid.paster import bootstrap, setup_logging
from sqlalchemy.exc import OperationalError

from ..views.login import hash_password
from ..models import User, Group, MetaDatum

def parse_args(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'config_uri',
        help='Configuration file, e.g., development.ini',
    )
    return parser.parse_args(argv[1:])

def create_initial_user(dbsession):
    admins = Group(
            id=0,
            name="Administrators"
            )
    root = User(
            id=0,
            enabled=True,
            email="admin@admin.admin",
            pwhash=hash_password("admin"),
            fullname="Administrator",
            group=admins)
    dbsession.add(root)

def create_example_metadata(dbsession):
    metadata = [
            MetaDatum(name = "#ID", mandatory=True),
            MetaDatum(name = "Date", mandatory=True),
            MetaDatum(name = "ZIP Code", mandatory=True),
            MetaDatum(name = "FileR1", mandatory=True),
            MetaDatum(name = "FileR2", mandatory=True)
            ]
    dbsession.add_all(metadata)

def main(argv=sys.argv):
    args = parse_args(argv)
    setup_logging(args.config_uri)
    env = bootstrap(args.config_uri)

    try:
        with env['request'].tm:
            dbsession = env['request'].dbsession

            # Create the initial admin user
            create_initial_user(dbsession)

            # Create example sample sheet columns
            create_example_metadata(dbsession)

    except OperationalError:
        print('''
Pyramid is having a problem using your SQL database.  The problem
might be caused by one of the following things:

1.  You may need to initialize your database tables with `alembic`.
    Check your README.txt for description and try to run it.

2.  Your database server may not be running.  Check that the
    database server referred to by the "sqlalchemy.url" setting in
    your "development.ini" file is running.
            ''')
