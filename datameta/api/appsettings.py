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
from pyramid.httpexceptions import HTTPNoContent, HTTPForbidden

from dataclasses import dataclass
from . import DataHolderBase
from typing import List
from ..models import ApplicationSetting
from .. import resource, security, errors
from ..security import authz
from ..resource import resource_by_id
from ..settings import get_setting_value_type
import datetime


@dataclass
class AppSettingsResponseElement(DataHolderBase):
    """Class for Appsettings Request Response from OpenApi"""
    id           : dict
    key          : str
    value_type   : str
    value        : str


@view_config(
    route_name="appsettings",
    renderer='json',
    request_method="GET",
    openapi=True
)
def get(request: Request) -> List[AppSettingsResponseElement]:
    """Return all Site Settings"""
    db = request.dbsession

    # Authenticate the user
    auth_user = security.revalidate_user(request)

    appsettings = db.query(ApplicationSetting)

    # User has to be site admin to access these settings
    if not authz.view_appsettings(auth_user):
        raise HTTPForbidden()

    settings = []

    for setting in appsettings:
        value, value_type = get_setting_value_type(setting)

        settings.append(
            AppSettingsResponseElement(
                id                    =  resource.get_identifier(setting),
                key                   =  setting.key,
                value_type             =  value_type,
                value                 =  value
            )
        )

    return settings


@view_config(
    route_name="appsettings_id",
    renderer='json',
    request_method="PUT",
    openapi=True
)
def put(request: Request):
    """Change an application setting"""
    auth_user = security.revalidate_user(request)
    db = request.dbsession
    settings_id = request.matchdict["id"]

    # Only site admins can change site settings
    if not authz.update_appsettings(auth_user):
        raise HTTPForbidden()

    target_setting = resource_by_id(db, ApplicationSetting, settings_id)

    temp, value_type = get_setting_value_type(target_setting)
    value = request.openapi_validated.body["value"]

    if value_type == 'int':
        try:
            value_int = int(value)
        except ValueError:
            raise errors.get_validation_error(["You have to provide an integer."])

        target_setting.int_value = value_int

    elif value_type == 'string':
        target_setting.str_value = value

    elif value_type == 'float':
        try:
            value_float = float(value)
        except ValueError:
            raise errors.get_validation_error(["You have to provide a float."])

        target_setting.float_value = value_float

    elif value_type == 'date':
        try:
            datetime.datetime.strptime(value, "%Y-%m-%d")
        except ValueError:
            raise errors.get_validation_error(["The date value has to specified in the form '%Y-%m-%d'."])

        target_setting.date_value = value

    elif value_type == 'time':
        try:
            datetime.datetime.strptime(value, "%H:%M:%S")
        except ValueError:
            raise errors.get_validation_error(["The time value has to specified in the form '%H:%M:%S'."])

        target_setting.date_value = value

    return HTTPNoContent()
