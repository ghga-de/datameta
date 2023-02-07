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

from datetime import datetime, timedelta
from typing import Optional
from random import choice
from string import ascii_letters, digits, punctuation

import bcrypt
import secrets
from pyramid.httpexceptions import HTTPFound, HTTPUnauthorized

from sqlalchemy import and_

from .tokenz import hash_token


from ..models import User, ApiKey, PasswordToken, Session, UsedPassword, LoginAttempt
from ..settings import get_setting

import logging
log = logging.getLogger(__name__)


def register_password(db, user_id, password):
    """ Hashes an accepted password string, adds the hash to the user's password hash history.

     Returns:
         - the hashed password
    """
    hashed_pw = hash_password(password)
    db.add(UsedPassword(user_id=user_id, pwhash=hashed_pw))

    return hashed_pw


def is_used_password(db, user_id, password):
    """ Checks a password string against a user's password hash history.

    Returns:
        - True, if password has been used before by the user
        - False, otherwise
    """

    used_passwords = db.query(UsedPassword).filter(UsedPassword.user_id == user_id).all()
    for pw in used_passwords:
        if check_password_by_hash(password, pw.pwhash):
            return True

    return False


def generate_token():
    return "".join(choice(ascii_letters + digits) for _ in range(64) )


def get_new_password_reset_token(db: Session, user: User, expires=None):
    """Clears all password recovery tokens for user identified by the supplied
    email address, generates a new one and returns it.

    Returns:
        - PasswordToken object (with hashed token value)
        - unhashed token value
    """

    # Delete existing tokens
    db.query(PasswordToken).filter(PasswordToken.user_id == user.id).delete()

    # Create new token value
    clear_token = secrets.token_urlsafe(40)

    # Add hashed token to db
    db_token_obj = PasswordToken(
            user=user,
            value=hash_token(clear_token),
            expires=expires if expires else datetime.now() + timedelta(minutes=10)
    )
    db.add(db_token_obj)

    return db_token_obj, clear_token


def get_new_password_reset_token_from_email(db: Session, email: str):
    """Clears all password recovery tokens for user identified by the supplied
    email address, generates a new one and returns it.

    Returns:
        - PasswordToken with hashed token value
        - cleartext token for user notification
    Raises:
        KeyError - if user not found/not enabled"""
    user = db.query(User).filter(User.enabled.is_(True), User.email == email).one_or_none()

    # User not found or disabled
    if not user:
        raise KeyError(f"Could not find active user with email={email}")

    return get_new_password_reset_token(db, user)


def check_expiration(expiration_datetime: Optional[datetime]):
    """Checks if an expiration date was exceeded. Returns true if expired."""
    return expiration_datetime is not None and datetime.now() >= expiration_datetime


def verify_password(db, user_id, password):
    """Checks if password matches security criteria
    as described in the application settings."""

    if is_used_password(db, user_id, password):
        return "The password has already been used."

    pw_min_length = get_setting(db, "security_password_minimum_length")
    pw_min_ucase = get_setting(db, "security_password_minimum_uppercase_characters")
    pw_min_lcase = get_setting(db, "security_password_minimum_lowercase_characters")
    pw_min_digits = get_setting(db, "security_password_minimum_digits")
    pw_min_punctuation = get_setting(db, "security_password_minimum_punctuation_characters")

    if len(password) < pw_min_length:
        return f"The password must be at least {pw_min_length} characters long."

    alphas = [c for c in password if c.isalpha()]
    digits = [c for c in password if c.isdigit()]
    puncs = [c for c in password if c in punctuation]
    n_upper = sum(c.isupper() for c in alphas)
    n_lower = len(alphas) - n_upper

    if n_upper < pw_min_ucase or n_lower < pw_min_lcase or len(digits) < pw_min_digits or len(puncs) < pw_min_punctuation:
        return f"Password must contain at least {pw_min_ucase} uppercase characters, " \
            f"{pw_min_lcase} lowercase character(s), " \
            f"{pw_min_punctuation} punctuation mark(s), and " \
            f"{pw_min_digits} digit(s)."

    invalid_chars = set(password).difference(alphas).difference(digits).difference(puncs)

    if invalid_chars:
        return f"Invalid password characters: {','.join(invalid_chars)}"

    return None


def hash_password(pw):
    """Hash a password and return the salted hash."""
    pwhash = bcrypt.hashpw(pw.encode('utf8'), bcrypt.gensalt())
    return pwhash.decode('utf8')


def check_password_by_hash(pw, hashed_pw):
    """Check a password against a salted hash."""
    expected_hash = hashed_pw.encode('utf8')
    return bcrypt.checkpw(pw.encode('utf8'), expected_hash)


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

    log.warning("Failed login attempt.", extra={"user_id": user.id, "failed_logins_last_hour": n_failed_logins})
    if n_failed_logins >= max_allowed_failed_logins:
        db.query(User).filter(user.id == User.id).update({User.enabled: False})
        db.flush()
        log.warning("User blocked due to repeated failed login attempts.", extra={"user_id": user.id, "user_enabled": user.enabled, "failed_logins_last_hour": n_failed_logins})

    return None


def get_user_by_credentials(request, email: str, password: str):
    """Check a combination of email and password, returns a user object if valid."""
    db = request.dbsession
    user = db.query(User).filter(and_(User.email == email, User.enabled.is_(True))).one_or_none()
    if user:
        if check_password_by_hash(password, user.pwhash):
            return user

        register_failed_login_attempt(db, user)

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
        except Exception:
            pass
    return None


def get_password_reset_token(db: Session, token: str):
    """Tries to find the corresponding password reset token in the database.
    Returns the token only if it can be found and if the corresponding user is
    enabled, otherwise no checking is performed, most importantly expiration
    checks are not performed"""
    return db.query(PasswordToken).join(User).filter(and_(
        PasswordToken.value == hash_token(token),
        User.enabled.is_(True)
        )).one_or_none()


def revalidate_user_token_based(request, token):
    """Revalidates user during token-based operations."""
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
            clear_failed_login_attempts(user=user, dbsession=db)
            return user

    raise HTTPUnauthorized()


def revalidate_user_session_based(request):
    """Revalidates user authentication in the current session."""

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
        request.session.invalidate()
        raise HTTPUnauthorized()

    request.session['site_admin'] = user.site_admin
    request.session['group_admin'] = user.group_admin

    clear_failed_login_attempts(user=user, dbsession=db)
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


def clear_failed_login_attempts(dbsession, user: User) -> None:
    """Sets number of login attempts to 0."""
    now = datetime.utcnow()
    attempts = dbsession.query(LoginAttempt).filter(LoginAttempt.user_id == user.id).all()
    logins_failed = len([now - attempt.timestamp <= timedelta(hours=1) for attempt in attempts])

    if logins_failed > 0:
        log.warning("Clearing failed login attempts.", extra={"user_id": user.id, "logins_failed": logins_failed})
        user.login_attempts.clear()
