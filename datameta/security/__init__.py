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

import logging

from datetime import datetime, timedelta
from typing import Optional

from pyramid.httpexceptions import HTTPFound, HTTPUnauthorized
from sqlalchemy import and_

from ..models import User, ApiKey, LoginAttempt
from ..settings import get_setting

from .pwdz import (  # noqa: F401
    register_password,
    is_used_password,
    verify_password,
    hash_password,
    check_password_by_hash
    )

from .tokenz import (  # noqa: F401
    generate_token,
    get_new_password_reset_token,
    get_new_password_reset_token_from_email,
    hash_token, get_bearer_token,
    get_password_reset_token
    )

log = logging.getLogger(__name__)


def check_expiration(expiration_datetime: Optional[datetime]):
    """
    Checks if an expiration date was exceeded. Returns true if expired.
    """
    return expiration_datetime is not None and datetime.now() >= expiration_datetime


def register_failed_login_attempt(db, user):
    """ Registers a failed login attempt and disables user if this has happened too often in the last hour."""

    now = datetime.utcnow()
    max_allowed_failed_logins = get_setting(db, "security_max_failed_login_attempts")

    db.add(LoginAttempt(user_id=user.id, timestamp=now))
    db.flush()
    n_failed_logins = sum(
        now - attempt.timestamp <= timedelta(hours=1)
        for attempt in db.query(LoginAttempt).filter(LoginAttempt.user_id == user.id).all()
    )

    log.warning(f"FAILED LOGIN ATTEMPT USER id={user.id} n={n_failed_logins} within one hour.")
    if n_failed_logins >= max_allowed_failed_logins:
        db.query(User).filter(user.id == User.id).update({User.enabled: False})
        db.flush()
        log.warning(f"BLOCKED USER id={user.id} enabled={user.enabled} reason={n_failed_logins} failed login attempts within one hour.")

    return None


def get_user_by_credentials(request, email: str, password: str):

    """Check a combination of email and password, returns a user object if valid"""

    db = request.dbsession
    user = db.query(User).filter(and_(User.email == email, User.enabled.is_(True))).one_or_none()
    if user:
        if check_password_by_hash(password, user.pwhash):
            log.warning(f"CLEARING FAILED LOGIN ATTEMPTS FOR gubc USER {user}")
            user.login_attempts.clear()
            return user

        register_failed_login_attempt(db, user)

    return None


def revalidate_user_token_based(request, token):
    db = request.dbsession

    token_hash = hash_token(token)
    apikey = db.query(ApiKey).join(User).filter(and_(
        ApiKey.value == token_hash,
        User.enabled.is_(True)
    )).one_or_none()

    if apikey is not None:
        apikey_expired = check_expiration(apikey.expires)
        user = apikey.user

        if apikey_expired:
            request.tm.abort()
            request.tm.begin()
            register_failed_login_attempt(db, user)
            request.tm.commit()
            request.tm.begin()
        else:
            log.warning(f"CLEARING FAILED LOGIN ATTEMPTS FOR APIKEY.USER {user.id}")
            user.login_attempts.clear()
            return user

    raise HTTPUnauthorized()


def revalidate_user_session_based(request):
    # Check for session based auth
    if 'user_uid' not in request.session:
        request.session.invalidate()
        raise HTTPUnauthorized()

    db = request.dbsession

    user = db.query(User).filter(and_(
        User.id == request.session['user_uid'],
        User.enabled.is_(True)
        )).one_or_none()

    # Check if the user still exists and their group hasn't changed
    if user is None or user.group_id != request.session['user_gid']:
        if user.group_id != request.session['user_gid']:
            request.tm.abort()
            request.tm.begin()
            register_failed_login_attempt(db, user)
            request.tm.commit()
            request.tm.begin()
        request.session.invalidate()
        raise HTTPUnauthorized()

    request.session['site_admin'] = user.site_admin
    request.session['group_admin'] = user.group_admin

    log.warning(f"CLEARING FAILED LOGIN ATTEMPTS FOR USER {user}")
    user.login_attempts.clear()
    return user


def revalidate_user(request):
    """Revalidate the currently logged in user and return the corresponding user object. On failure,
    raise a 401"""

    # Check for token based auth
    token = get_bearer_token(request)
    if token is not None:
        return revalidate_user_token_based(request, token)

    return revalidate_user_session_based(request)


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
