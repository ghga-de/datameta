# Copyright 2021 Universität Tübingen
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

import secrets
from datetime import datetime, timedelta

from .models import PasswordToken

def new_token(db, user_id):
    """Clears all password recovery tokens for the specified user ID, generates a new one and returns it"""
    # Delete existing tokens
    db.query(PasswordToken).filter(PasswordToken.user_id==user_id).delete()

    # Create new token value
    value = secrets.token_urlsafe(40)

    # Insert token
    pass_token = PasswordToken(
            user_id=user_id,
            value=value,
            expires=datetime.now() + timedelta(minutes=10)
            )
    db.add(pass_token)

    return value
