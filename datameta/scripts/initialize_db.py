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
    parser.add_argument('-c', '--config_uri', required=True, help='Configuration file, e.g., development.ini')
    parser.add_argument('-un', '--initial-user-fullname', required=True, type=str, help='Full name of the initial user')
    parser.add_argument('-ue', '--initial-user-email', required=True, type=str, help='Email address of the initial user')
    parser.add_argument('-up', '--initial-user-pass', required=True, type=str, help='Password of the initial user')
    parser.add_argument('-g', '--initial-group', required=True, type=str, help='Name of the initial group')
    return parser.parse_args(argv[1:])

def create_initial_user(request, email, fullname, password, groupname):
    from .. import siteid

    db = request.dbsession
    # Perform initialization only if the group table is empty
    if (db.query(Group.id).count() == 0):
        init_group = Group(
                id=0,
                name=groupname,
                site_id=siteid.generate(request, Group)
                )
        root = User(
                id=0,
                site_id=siteid.generate(request, User),
                enabled=True,
                email=email,
                pwhash=hash_password(password),
                fullname=fullname,
                group=init_group,
                group_admin=True,
                site_admin=True
                )
        db.add(root)

def create_example_metadata(dbsession):
    if dbsession.query(MetaDatum).first() is None:
        metadata = [
                MetaDatum(name = "#ID",
                    mandatory=True,
                    order=100,
                    isfile=False,
                    regexp=r"^[A-Z][A-Z][0-9][0-9]$",
                    lintmessage="The ID must be specified as two uppercase characters followed by two digits."),
                MetaDatum(name = "Date",
                    mandatory=True,
                    order=200,
                    datetimefmt="%Y-%m-%d",
                    datetimemode=DateTimeMode.DATE,
                    isfile=False),
                MetaDatum(name = "ZIP Code",
                    mandatory=True,
                    order=300,
                    isfile=False,
                    regexp=r"^[0-9][0-9][0-9]$",
                    lintmessage="Please specify the first three digits of the ZIP code",
                    ),
                MetaDatum(name = "FileR1",
                    mandatory=True,
                    order=400,
                    isfile=True),
                MetaDatum(name = "FileR2",
                    mandatory=True,
                    order=500,
                    isfile=True)
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


def create_default_site_settings(db):
    db.add(ApplicationSettings(
        key='logo_html',
        str_value = '<p class="h4 my-0 me-md-auto fw-normal" style="font-family: \'Fira Sans\', sans-serif;"><a href="/" class="link-bare"><span style="color:#ffca2c">D</span>ata<span style="color:#ffca2c">M</span>eta</a></p>'
        ))

def main(argv=sys.argv):
    args = parse_args(argv)

    setup_logging(args.config_uri)
    env = bootstrap(args.config_uri)

    try:
        with env['request'].tm:
            dbsession = env['request'].dbsession

            # Check if a user exists, if so don't initialize
            if dbsession.query(User).first() is not None:
                print("Database appears to already have data. Not inserting any defaults.", file=sys.stderr)
                sys.exit(0)

            # Check that specified defaults aren't empty strings (e.g. from the shipped compose file)
            for arg in ['initial_user_fullname','initial_user_email','initial_user_pass','initial_group']:
                if not vars(args)[arg]:
                    sys.exit(f"Please specify a valid string for '{arg}'!")

            # Create the initial admin user
            create_initial_user(env['request'], args.initial_user_email, args.initial_user_fullname, args.initial_user_pass, args.initial_group)

            # Create example sample sheet columns
            create_example_metadata(dbsession)

            # Create email templates
            create_email_templates(dbsession)

            # Create default site settings
            create_default_site_settings(dbsession)

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
