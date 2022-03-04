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

import bcrypt
import logging

from string import punctuation

from pyramid.httpexceptions import HTTPFound, HTTPUnauthorized
from sqlalchemy import and_

from ..models import UsedPassword
from ..settings import get_setting

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


def verify_password(db, user_id, password):
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
    """Hash a password and return the salted hash"""
    pwhash = bcrypt.hashpw(pw.encode('utf8'), bcrypt.gensalt())
    return pwhash.decode('utf8')


def check_password_by_hash(pw, hashed_pw):
    """Check a password against a salted hash"""
    expected_hash = hashed_pw.encode('utf8')
    return bcrypt.checkpw(pw.encode('utf8'), expected_hash)
