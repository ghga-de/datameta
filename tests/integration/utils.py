"""Module containing utility functions and classes for
use in the test framework.
"""
from typing import Optional
from dataclasses import dataclass
import transaction
from copy import deepcopy
from .fixtures import UserFixture, MetaDatumFixture, AuthFixture
from datetime import datetime, timedelta

from datameta import models, security
from datameta.models import get_tm_session
import secrets

from datameta.security import get_new_password_reset_token

def get_group_by_name(
    session_factory,
    group_name
):
    with transaction.manager:
        session = get_tm_session(session_factory, transaction.manager)
        group_obj = session.query(models.Group).filter(models.Group.name==group_name).one_or_none()

        assert group_obj, f"I don't know this group: {group_name}"

        return group_obj.uuid

def get_user_by_uuid(
    session_factory,
    user_uuid
):
    with transaction.manager:
        session = get_tm_session(session_factory, transaction.manager)
        user_obj = session.query(models.User).filter(models.User.uuid==user_uuid).one_or_none()

        assert user_obj, f"I don't know this user: {str(user_uuid)}"

        user_vals = dict()
        for attr in ("fullname", "enabled", "site_admin", "group_admin"):
            json_val = "".join(item.capitalize() if i else item for i, item in enumerate(attr.split("_")))
            user_vals[json_val] = getattr(user_obj, attr)
        user_vals["group_uuid"] = str(user_obj.group.uuid)

        return user_vals


def create_pwtoken(
    session_factory,
    user,
    expires=datetime.now() + timedelta(minutes=10)
):
    """ Add a valid (default) or expiring (set timedelta + sleep) password reset token to the database.
    CAVEATS:
     - 1 / user (unless database is reset between individual pw-reset tests)
    """
    with transaction.manager:
        session = get_tm_session(session_factory, transaction.manager)
        user_obj = session.query(models.User).filter(models.User.uuid==user.uuid).one_or_none()

        if not user_obj:
            assert False, f"I don't know this user: {str(user)}"

        _, token = get_new_password_reset_token(session, user=user_obj, expires=expires)
        session.flush()

        return token

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

        # add token:
        now = datetime.now()
        future = now + timedelta(hours=100)
        token = security.generate_token()
        token_obj = models.ApiKey(
            user_id = user_obj.id,
            value = security.hash_token(token),
            label = "valid_token",
            expires = future
        )
        session.add(token_obj)
        session.flush()

        # add expired token:
        now = datetime.now()
        past = now - timedelta(hours=100)
        expired_token = security.generate_token()
        expired_token_obj = models.ApiKey(
            user_id = user_obj.id,
            value = security.hash_token(expired_token),
            label = "expired_token",
            expires = past
        )
        session.add(expired_token_obj)
        session.flush()


        # return user updated with uuid and tokens:
        user_updated = deepcopy(user)
        user_updated.uuid = str(user_obj.uuid)
        user_updated.group_site_id = group_obj.site_id
        user_updated.group_uuid = str(group_obj.uuid)
        user_updated.auth = AuthFixture(token, token_obj.uuid)
        user_updated.expired_auth = AuthFixture(expired_token, expired_token_obj.uuid)
        return user_updated


def create_metadatum(
    session_factory,
    metadatum:MetaDatumFixture
):
    """Add a metadatum to the database"""
    with transaction.manager:
        session = get_tm_session(session_factory, transaction.manager)
        
        # create metadatum:
        metadatum_obj = models.MetaDatum(
            name = metadatum.name,
            mandatory = metadatum.mandatory,
            order = metadatum.order,
            isfile = metadatum.isfile,
            site_unique = metadatum.site_unique,
            submission_unique = metadatum.submission_unique,
            datetimefmt = metadatum.datetimefmt,
            datetimemode = metadatum.datetimemode,
            regexp = metadatum.regexp,
            example = metadatum.example,
            short_description = metadatum.short_description, 
            long_description = metadatum.long_description
        )
        session.add(metadatum_obj)
        session.flush()

        # return user updated with uuid:
        metadatum_updated = deepcopy(metadatum_obj)
        metadatum_updated.uuid = str(metadatum_updated.uuid)
        return metadatum_updated


def set_application_settings(
    session_factory
):
    """Set application settings in the db."""
    with transaction.manager:
        session = get_tm_session(session_factory, transaction.manager)
        
        # creat logo_html:
        logo_html = models.ApplicationSettings(
            key='logo_html',
            str_value = '<p></p>'
        )
        session.add(logo_html)
        session.flush()
