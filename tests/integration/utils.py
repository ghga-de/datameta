"""Module containing utility functions and classes for
use in the test framework.
"""
from typing import Optional
from dataclasses import dataclass
import transaction
from copy import deepcopy
from .fixtures import UserFixture, MetaDatumFixture
from datetime import datetime, timedelta

from datameta import models, security
from datameta.models import get_tm_session

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
        user_updated.token = token
        user_updated.expired_token = expired_token
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


def get_auth_headers(token:str):
    """Generate header with Bearer authentication from token"""
    return {
        "Authorization": f"Bearer {token}"
    }