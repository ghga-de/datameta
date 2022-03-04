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

import hashlib
import logging
import secrets

from datetime import datetime, timedelta
from random import choice
from string import ascii_letters, digits

from sqlalchemy import and_

from ..models import User, PasswordToken, Session


log = logging.getLogger(__name__)


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


def hash_token(token):
    """Hash a token and return the unsalted hash"""
    hashed_token = hashlib.sha256(token.encode('utf-8')).hexdigest()
    return hashed_token


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
