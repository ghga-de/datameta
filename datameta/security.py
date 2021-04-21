# Copyright 2021 Universität Tübingen, DKFZ and EMBL for the German Human Genome-Phenome Archive (GHGA)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from pyramid.httpexceptions import HTTPFound, HTTPUnauthorized
from datetime import datetime, timedelta
from typing import Optional
from random import choice
from string import ascii_letters, digits
from sqlalchemy import and_

from .models import User, ApiKey, PasswordToken, Session, MetaDataSet


import bcrypt
import hashlib
import logging
import secrets
log = logging.getLogger(__name__)

def generate_token():
    return "".join(choice(ascii_letters+digits) for _ in range(64) )

def get_new_password_reset_token(db:Session, user:User, expires=None):
    """Clears all password recovery tokens for user identified by the supplied
    email address, generates a new one and returns it.

    Returns:
        - PasswordToken object (with hashed token value)
        - unhashed token value
    """

    # Delete existing tokens
    db.query(PasswordToken).filter(PasswordToken.user_id==user.id).delete()

    # Create new token value
    clear_token = secrets.token_urlsafe(40)

    # Add hashed token to db
    db_token_obj = PasswordToken(
            user=user,
            value=hash_token(clear_token),
            expires=expires if expires else datetime.now() + timedelta(minutes=10)
    )
    db.add(db_token_obj)

    return db_token_obj, clear_token

def get_new_password_reset_token_from_email(db:Session, email:str):
    """Clears all password recovery tokens for user identified by the supplied
    email address, generates a new one and returns it.

    Returns:
        - PasswordToken with hashed token value
        - cleartext token for user notification
    Raises:
        KeyError - if user not found/not enabled"""
    user = db.query(User).filter(User.enabled == True, User.email == email).one_or_none()

    # User not found or disabled
    if not user:
        raise KeyError(f"Could not find active user with email={email}")

    return get_new_password_reset_token(db, user)

def check_expiration(expiration_datetime:Optional[datetime]):
    """
    Checks if an expiration date was exceeded. Returns true if expired.
    """
    return expiration_datetime is not None and datetime.now() >= expiration_datetime

def verify_password(s):
    if len(s)<10:
        return "The password has to have a length of at least 10 characters."
    return None

def hash_password(pw):
    """Hash a password and return the salted hash"""
    pwhash = bcrypt.hashpw(pw.encode('utf8'), bcrypt.gensalt())
    return pwhash.decode('utf8')

def check_password_by_hash(pw, hashed_pw):
    """Check a password against a salted hash"""
    expected_hash = hashed_pw.encode('utf8')
    return bcrypt.checkpw(pw.encode('utf8'), expected_hash)

def hash_token(token):
    """Hash a token and return the unsalted hash"""
    hashed_token =  hashlib.sha256(token.encode('utf-8')).hexdigest()
    return hashed_token

def get_user_by_credentials(request, email:str, password:str):
    """Check a combination of email and password, returns a user object if valid"""
    db = request.dbsession
    user = db.query(User).filter(and_(User.email==email, User.enabled==True)).one_or_none()
    if user and check_password_by_hash(password, user.pwhash):
        return user
    return None

def get_bearer_token(request):
    """Extracts a Bearer authentication token from the request and returns it if present, None
    otherwise."""
    auth = request.headers.get("Authorization")
    if auth is not None:
        try:
            method, content = auth.split(" ")
            if method == "Bearer":
                return content
        except:
            pass
    return None

def get_password_reset_token(db:Session, token:str):
    """Tries to find the corresponding password reset token in the database.
    Returns the token only if it can be found and if the corresponding user is
    enabled, otherwise no checking is performed, most importantly expiration
    checks are not performed"""
    return db.query(PasswordToken).join(User).filter(and_(
        PasswordToken.value == hash_token(token),
        User.enabled == True
        )).one_or_none()

def revalidate_user(request):
    """Revalidate the currently logged in user and return the corresponding user object. On failure,
    raise a 401"""
    db = request.dbsession
    # Check for token based auth
    token = get_bearer_token(request)
    if token is not None:
        token_hash = hash_token(token)
        apikey = db.query(ApiKey).join(User).filter(and_(
            ApiKey.value == token_hash,
            User.enabled == True
            )).one_or_none()
        if apikey is not None:
            if check_expiration(apikey.expires):
                raise HTTPUnauthorized()
            return apikey.user
        else:
            raise HTTPUnauthorized()

    # Check for session based auth
    if 'user_uid' not in request.session:
        request.session.invalidate()
        raise HTTPUnauthorized()
    user = request.dbsession.query(User).filter(and_(
        User.id == request.session['user_uid'],
        User.enabled == True
        )).one_or_none()
    # Check if the user still exists and their group hasn't changed
    if user is None or user.group_id != request.session['user_gid']:
        request.session.invalidate()
        raise HTTPUnauthorized()
    request.session['site_admin'] = user.site_admin
    request.session['group_admin'] = user.group_admin
    return user

def revalidate_user_or_login(request):
    """Revalidate and return the currently logged in user, on failure redirect to the login page"""
    try:
        return revalidate_user(request)
    except HTTPUnauthorized:
        raise HTTPFound("/login")

def revalidate_admin(request):
    """Revalidate the currently logged in user and return the corresponding user object. On failure
    or if the user is not a site or group admin, raise a 403"""
    user = revalidate_user(request)
    if user.site_admin or user.group_admin:
        return user
    raise HTTPUnauthorized()

def is_self_user_action(user, target_user):
    return user.uuid == target_user.uuid

def has_group_rights(user, group):
    return user.site_admin or (user.group_admin and user.group.uuid == group.uuid)

def is_authorized_groupname_change(user):
    return user.site_admin

def is_authorized_group_submission_view(user, group_id):
    # Only members of a group are allowed to view its submissions (what about the site admin??)
    return group_id in [user.group.uuid, user.group.site_id]

def is_authorized_data_access(user, data_obj):
    return user.id == data_obj.user_id

def is_authorized_file_deletion(user, file_obj):
    return is_authorized_data_access(user, file_obj)
def is_authorized_file_update(user, file_obj):
    return is_authorized_data_access(user, file_obj)

def is_authorized_file_submission(user, file_obj):
    return is_authorized_data_access(user, file_obj)
def is_authorized_mds_submission(user, mds_obj):
    return is_authorized_data_access(user, mds_obj)


def is_authorized_metadatum_update(user):
    return user.site_admin
def is_authorized_metadatum_creation(user):
    return user.site_admin

def is_authorized_mds_deletion(user, mdata_set):
    return user.id == mdata_set.user_id
    
def is_authorized_data_view(user, data_user_id, data_group_id, was_submitted=False):
    # if dataset was already submitted, the group must match
    # if dataset was not yet submitted, the user must match
    return any((
        (was_submitted and data_group_id == user.group_id),
        (not was_submitted and data_user_id == user.id)
    ))

def is_authorized_file_view(user, file_obj):
    was_submitted = (
        file_obj.content_uploaded and 
        file_obj.metadatumrecord and  
        file_obj.metadatumrecord.metadataset.submission_id 
    )
    group_id = file_obj.metadatumrecord.metadataset.submission.group_id if was_submitted else None
    return is_authorized_data_view(user, file_obj.user_id, group_id, was_submitted=was_submitted)
    
def is_authorized_mds_view(user, mds_obj):
    was_submitted = bool(mds_obj.submission_id is not None)
    group_id = mds_obj.submission.group_id if was_submitted else None
    return is_authorized_data_view(user, mds_obj.user_id, group_id, was_submitted=was_submitted)
    

def check_metadata_access(metadataset_obj:MetaDataSet, user:User):
    if metadataset_obj.submission_id:
        # if metadataset was already submitted, the group must match
        return metadataset_obj.submission.group_id == user.group_id
    else:
        # if metadataset was not yet submitted, the user must match
        return metadataset_obj.user_id == user.id

def is_authorized_apikey_view(user, target_user):
    return is_self_user_action(user, target_user)
def is_authorized_apikey_deletion(user, target_user):
    return is_self_user_action(user, target_user)

def is_authorized_appsettings_view(user):
    return user.site_admin
def is_authorized_appsettings_update(user):
    return user.site_admin

def is_authorized_password_change(user, target_user):
    return is_self_user_action(user, target_user)


def is_authorized_group_change(user):
    return user.site_admin
def is_authorized_grant_siteadmin(user, target_user):
    return user.site_admin and not is_self_user_action(user, target_user)
def is_authorized_grant_groupadmin(user, target_user):
    # group admin can revoke its own group admin status?
    return has_group_rights(user, target_user.group)
def is_authorized_status_change(user, target_user):
    return all((
        has_group_rights(user, target_user.group),
        not is_power_grab(user, target_user),
        not is_self_user_action(user, target_user)
    ))
def is_authorized_name_change(user, target_user):
    return any((
        has_group_rights(user, target_user.group),
        is_self_user_action(user, target_user)
    ))
    # not (has_admin_rights or edit_own_user):


def is_power_grab(user, target_user):
    return not user.site_admin and target_user.site_admin

    #has_admin_rights

    #has_group_rights = auth_user.group_admin and auth_user.group.uuid == target_user.group.uuid
    #has_admin_rights = auth_user.site_admin or has_group_rights
    #edit_own_user = auth_user.uuid == target_user.uuid