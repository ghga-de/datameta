# Copyright (c) 2021 Universität Tübingen, Germany
# Authors: Leon Kuchenbecker <leon.kuchenbecker@uni-tuebingen.de>,
#          Moritz Hahn <moritz.hahn@uni-tuebingen.de>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from pyramid.view import view_config
from pyramid.request import Request
from pyramid.httpexceptions import HTTPNoContent, HTTPForbidden, HTTPBadRequest

from dataclasses import dataclass
from . import DataHolderBase
from typing import List, Dict
from ..models import ApplicationSettings
from .. import resource, security, errors
from ..resource import resource_by_id
from ..settings import get_setting_value_type
import datetime

@dataclass
class AppSettingsResponseElement(DataHolderBase):
    """Class for Appsettings Request Response from OpenApi"""
    id:         dict
    key:        str
    value_type:  str
    value:      str

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

    appsettings = db.query(ApplicationSettings)

    # User has to be site admin to access these settings
    if not auth_user.site_admin:
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
def put(request:Request):
    """Change a metadataset"""
    auth_user = security.revalidate_user(request)
    db = request.dbsession
    settings_id = request.matchdict["id"]

    # Only site admins can change site settings
    if not auth_user.site_admin:
         raise HTTPForbidden()

    target_setting = resource_by_id(db, ApplicationSettings, settings_id)

    key = request.openapi_validated.body["key"]
    temp, value_type = get_setting_value_type(target_setting)
    value = request.openapi_validated.body["value"]

    if value_type == 'int':
        try:
            value_int = int(value)
        except ValueError:
            err = {
                "exception": "ValidationError",
            }   
            response_body = []
            err["message"] = "You have to provide an integer."
            response_body.append(err)
            return HTTPBadRequest(json=response_body)
            
        target_setting.key = key
        target_setting.int_value = value_int

    elif value_type == 'string':
        target_setting.key = key
        target_setting.str_value = value

    elif value_type == 'float':
        try:
            value_float_float = float(value)
        except ValueError:
            err = {
                "exception": "ValidationError",
            }   
            response_body = []
            err["message"] = "You have to provide a float."
            response_body.append(err)
            return HTTPBadRequest(json=response_body)
            
        target_setting.key = key
        target_setting.float_value = value_float

    elif value_type == 'date':
        try: 
            datetime.datetime.strptime(value,"%Y-%m-%d")
        except ValueError:
            err = {
                "exception": "ValidationError",
            }   
            response_body = []
            err["message"] = "The date type has to specified in the form '%Y-%m-%d'."
            response_body.append(err)
            return HTTPBadRequest(json=response_body)

        target_setting.key = key
        target_setting.date_value = value

    elif value_type == 'time':
        try: 
            datetime.datetime.strptime(value,"%H:%M:%S")
        except ValueError:
            err = {
                "exception": "ValidationError",
            }   
            response_body = []
            err["message"] = "The time type has to specified in the form '%H:%M:%S'."
            response_body.append(err)
            return HTTPBadRequest(json=response_body)

        target_setting.key = key
        target_setting.date_value = value

    else: 
        err = {
            "exception": "ValidationError",
        }   
        response_body = []
        err["message"] = "The value type of this setting is not defined."
        response_body.append(err)
        return HTTPBadRequest(json=response_body)

    return HTTPNoContent()