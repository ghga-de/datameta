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
import secrets

from cryptography.fernet import Fernet
import pyotp
import qrcode
import qrcode.image.svg
from sqlalchemy import and_
from pyramid import threadlocal
from pyramid.settings import asbool

from . import hash_token
from ..models import User, Session, TfaToken
from ..settings import get_setting

import logging
log = logging.getLogger(__name__)


def is_2fa_enabled():
    """Check if the system has 2fa enabled.

    Returns:
        - the 2fa activation status
    """
    return asbool(threadlocal.get_current_registry().settings['datameta.tfa.enabled'])


def get_2fa_crypto_function():
    """Get the encrypt/decrypt function based on the system's master key.

    Returns:
        - a Fernet crypto function object

    """
    encrypt_key = str(threadlocal.get_current_registry().settings['datameta.tfa.encrypt_key'])
    return Fernet(encrypt_key.encode())


def generate_2fa_secret(db):
    """Generate and encrypt a 2fa secret.

    Returns:
          - the encrypted 2fa secret as a string
    """

    encrypt_f = get_2fa_crypto_function(db).encrypt
    return encrypt_f(pyotp.random_base32().encode()).decode()


def unpack_2fa_secret(db, secret):
    """Decrypt and decode a 2fa secret.

    Returns:
        - the decrypted and decoded secret
    """

    decrypt_f = get_2fa_crypto_function(db).decrypt
    return decrypt_f(secret.encode()).decode()


def generate_totp_uri(db, user, secret):
    """Generates a totp uri for the given user.

    Returns:
        - the totp uri
        - None if the user has no 2fa secret
    """

    if user.tfa_secret is None:
        return None

    issuer = str(threadlocal.get_current_registry().settings['datameta.tfa.otp_issuer'])
    return pyotp.totp.TOTP(unpack_2fa_secret(db, secret)).provisioning_uri(
        name=user.email,
        issuer_name=issuer
    )


def generate_2fa_qrcode(db, user, secret):
    """Generates a qr code in svg format encoding the totp uri for the given user.

    Returns:
        - a string containing the svg d-attribute encoding the qr code
        - an empty string if the user has no 2fa secret
    """

    if user.tfa_secret is None:
        return ""

    totp_uri = generate_totp_uri(db, user, secret)
    qr_code = qrcode.make(totp_uri, image_factory=qrcode.image.svg.SvgPathFillImage)
    return qr_code.make_path().get("d")


def get_user_2fa_secret(db, user):
    """Decrypts and returns the 2fa secret for the given user.

    Returns:
        - the decrypted 2fa secret string
        - None if the user has no 2fa secret
    """

    if user.tfa_secret is None:
        return None

    decrypt_f = get_2fa_crypto_function(db)
    secret = decrypt_f.decrypt(user.tfa_secret.encode())
    return secret.decode()


def verify_otp(db, secret, otp_token):
    """Verifies an otp token against a secret.

    Returns:
    - None if otp is verified
    - a message string if not
    """

    if not pyotp.TOTP(unpack_2fa_secret(db, secret)).verify(otp_token):
        return "The OTP does not match the expected value."
    return None


def create_2fa_token(db: Session, user: User, expires=None):
    """Clears all existing 2fa setup tokens for user,
    generates a new token and returns it.

    Returns:
         - TfaToken object with hashed token value
         - unhashed ('clear') token value
    """

    # Delete existing tokens
    db.query(TfaToken).filter(TfaToken.user_id == user.id).delete()

    clear_token = secrets.token_urlsafe(40)

    token = TfaToken(
        user_id=user.id,
        value=hash_token(clear_token),
        expires=expires if expires else datetime.now() + timedelta(minutes=10),
        secret=generate_2fa_secret(db)
    )
    db.add(token)

    return clear_token, token


def check_2fa_token(db: Session, token: str):
    """Tries to find the corresponding password reset token in the database.
    Returns the token only if it can be found and if the corresponding user is
    enabled, otherwise no checking is performed, most importantly expiration
    checks are not performed.

    Returns:
        - the token if it exists else None
    """
    return db.query(TfaToken).join(User).filter(and_(
        TfaToken.value == hash_token(token),
        User.enabled.is_(True)
    )).one_or_none()
