import argparse
import sys
import random
import uuid

from pyramid.paster import bootstrap, setup_logging
from sqlalchemy.exc import OperationalError

from ..security import hash_password
from ..models import User, Group, MetaDatum, DateTimeMode, ApplicationSettings

def parse_args(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'config_uri',
        help='Configuration file, e.g., development.ini',
    )
    return parser.parse_args(argv[1:])

def create_initial_user(dbsession):
    # Perform initialization only if the group table is empty
    rnd = list(str(uuid.uuid4()).replace("-", ""))
    random.shuffle(rnd)
    newpass = "admin_" + "".join(rnd[:5])
    if (dbsession.query(Group.id).count() == 0):
        init_group = Group(
                id=0,
                name="My Organization"
                )
        root = User(
                id=0,
                enabled=True,
                email="admin@admin.admin",
                pwhash=hash_password(newpass),
                fullname="Administrator",
                group=init_group,
                group_admin=True,
                site_admin=True
                )
        dbsession.add(root)
        print(f"""\
+
+
+
INITIAL USER CREATED! EMAIL 'admin@admin.admin' PASS '{newpass}'
+
+
+""", file = sys.stderr)

def create_example_metadata(dbsession):
    if dbsession.query(MetaDatum).first() is None:
        metadata = [
                MetaDatum(name = "#ID", mandatory=True, order=100, isfile=False),
                MetaDatum(name = "Date", mandatory=True, order=200, datetimefmt="%Y-%m-%d", datetimemode=DateTimeMode.DATE, isfile=False),
                MetaDatum(name = "ZIP Code", mandatory=True, order=300, isfile=False),
                MetaDatum(name = "FileR1", mandatory=True, order=400, isfile=True),
                MetaDatum(name = "FileR2", mandatory=True, order=500, isfile=True)
                ]
        dbsession.add_all(metadata)

def create_email_templates(db):
    keys = [ row[0] for row in db.query(ApplicationSettings.key) ]

    # EMAIL TEMPLATE: FORGOT -> TOKEN
    if "subject_forgot_token" not in keys:
        db.add(ApplicationSettings(
            key = "subject_forgot_token",
            str_value= "Your password recovery request"))

    if "template_forgot_token" not in keys:
        db.add(ApplicationSettings(
            key = "template_forgot_token",
            str_value=
"""Dear {fullname},

a new password was requested for your account. If you did not issue this request, you can safely ignore this email. Otherwise, you can use the following link below to create a new password:

{token_url}

Best regards,
The Support Team"""))

    # EMAIL TEMPLATE: WELCOME -> TOKEN
    if "subject_welcome_token" not in keys:
        db.add(ApplicationSettings(
            key = "subject_welcome_token",
            str_value= "Your registration was confirmed!"))
    if "template_welcome_token" not in keys:
        db.add(ApplicationSettings(
            key = "template_welcome_token",
            str_value=
"""Dear {fullname},

your registration has been confirmed! Please use the following link to set a password for your account:

{token_url}

If you experience any difficulties logging in, please do not hesitate to contact the support team.

Best regards,
The Support Team"""))

    # EMAIL TEMPLATE: REJECT REGISTRATION
    if "subject_reject" not in keys:
        db.add(ApplicationSettings(
            key = "subject_reject",
            str_value= "Your registration request was rejected"))
    if "template_reject" not in keys:
        db.add(ApplicationSettings(
            key = "template_reject",
            str_value=
"""Dear {fullname},

we regret to inform you that your registration request has been rejected.

Best regards,
The Support Team"""))


    # EMAIL TEMPLATE: NEW REGISTRATION REQUEST ADMIN NOTIFY
    if "subject_reg_notify" not in keys:
        db.add(ApplicationSettings(
            key = "subject_reg_notify",
            str_value= "New registration request"))
    if "template_reg_notify" not in keys:
        db.add(ApplicationSettings(
            key = "template_reg_notify",
            str_value=
"""Dear administrator,

a new registration request has been issued:

Name: {req_fullname}
Email: {req_email}
Organization: {req_group}

Follow the following link to respond to the registration request:

{req_url}

Best regards,
The Support Team"""))


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

            # Create email templates
            create_email_templates(dbsession)

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
