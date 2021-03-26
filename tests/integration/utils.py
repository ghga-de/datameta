"""Module containing utility functions and classes for
use in the test framework.
"""
from typing import Optional
from dataclasses import dataclass
import transaction
from copy import deepcopy
from .fixtures import UserFixture

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

        # return user updated with uuid:
        user_updated = deepcopy(user)
        user_updated.uuid = str(user_obj.uuid)
        return user_updated


def get_auth_headers(token:str):
    """Generate header with Bearer authentication from token"""
    return {
        "Authorization": f"Bearer {token}"
    }