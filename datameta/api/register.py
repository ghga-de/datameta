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

from pyramid.view import view_config
from pyramid.request import Request
from pyramid.httpexceptions import HTTPNoContent

from dataclasses import dataclass
from ..models import Group, ApplicationSetting, User, RegRequest
from . import DataHolderBase
from .. import email, errors
from ..resource import get_identifier, resource_by_id
from sqlalchemy import or_, and_
from ..settings import get_setting
import re
from typing import Optional

import logging
log = logging.getLogger(__name__)


@dataclass
class RegisterOptionsResponse(DataHolderBase):
    user_agreement: str
    groups: list


@view_config(
    route_name="register_settings",
    renderer='json',
    request_method="GET",
    openapi=True
)
def get(request: Request) -> RegisterOptionsResponse:

    db = request.dbsession

    user_agreement = db.query(ApplicationSetting).filter(ApplicationSetting.key == "user_agreement").first()
    groups = db.query(Group)

    if user_agreement is not None:
        user_agreement = str(user_agreement.str_value)

    return RegisterOptionsResponse(
        user_agreement = user_agreement,
        groups = [ {"id": get_identifier(group), "name": group.name} for group in groups ]
    )


def get_authorative_admins(db, reg_request):
    """Identifies administrative users that are authorative for a given
    registration request and returns the corresponding database user objects"""
    if reg_request.group_id is None:
        return db.query(User).filter(User.site_admin.is_(True)).all()
    else:
        return db.query(User).filter(or_(
            User.site_admin.is_(True),
            and_(User.group_admin.is_(True), User.group_id == reg_request.group_id)
            )).all()


@view_config(
    route_name='register_submit',
    renderer='json',
    request_method="POST",
    openapi=True
)
def post(request):

    db = request.dbsession
    error_fields = []
    name = request.openapi_validated.body['name']
    req_email = request.openapi_validated.body['email'].lower()
    org_select = request.openapi_validated.body['org_select']
    org_create = request.openapi_validated.body['org_create'] is not None
    org_new_name = request.openapi_validated.body['org_new_name']
    check_user_agreement = request.openapi_validated.body['check_user_agreement']

    # check, if a user agreement exists
    user_agreement = db.query(ApplicationSetting).filter(ApplicationSetting.key == "user_agreement").first()

    if str(user_agreement.str_value) == '':
        check_user_agreement = True

    # Check, if the user accepted the user agreement
    if not check_user_agreement:
        error_fields.append('check_user_agreement')

    # Basic validity check for email
    if not re.match(r"[^@]+@[^@]+\.[^@]+", req_email):
        error_fields.append('email')
    else:
        # Check if the user already exists
        if db.query(User).filter(User.email == req_email).one_or_none() is not None:
            error_fields.append('user_exists')
        elif db.query(RegRequest).filter(RegRequest.email == req_email).one_or_none() is not None:
            error_fields.append('req_exists')

    # Check whether the selected organization is valid
    if org_create:
        if not org_new_name:
            error_fields.append('org_new_name')
    else:
        group_ : Optional[Group] = resource_by_id(db, Group, org_select)
        if group_ is None:
            error_fields.append('org_select')
        else:
            group : Group = group_

    # Check whether a name was specified
    if not name:
        error_fields.append('name')

    # If errors occurred, return them
    if error_fields:
        raise errors.get_validation_error(fields=error_fields, messages=['' for _ in error_fields])

    # Store a new registration request in the database
    reg_req = RegRequest(
            fullname = name,
            email = req_email,
            group_id = None if org_create else group.id,
            new_group_name = None if not org_create else org_new_name
            )
    db.add(reg_req)
    db.flush()

    # Send out a notification to authorative admins
    admins = get_authorative_admins(db, reg_req)
    email.send(
            recipients = email.__smtp_from,
            subject = get_setting(db, "subject_reg_notify"),
            template = get_setting(db, "template_reg_notify"),
            values = {
                'req_fullname' : reg_req.fullname,
                'req_email' : reg_req.email,
                'req_group' : reg_req.new_group_name if org_create else group.name,
                'req_url' : request.route_url('admin') + f"?showreq={reg_req.uuid}"
                },
            bcc = [ admin.email for admin in admins ],
            rec_header_only=True  # We're not actually sending this to the from address, just using it in the "To" header
            )

    if org_create:
        log.info("New registration request.", extra={"req_email": req_email, "req_name": name, "req_group": org_new_name, "is_new_group": True})
    else:
        log.info("New registration request.", extra={"req_email": req_email, "req_name": name, "req_group": group.name, "is_new_group": False})
    return HTTPNoContent()
