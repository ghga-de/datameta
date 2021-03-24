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
import datetime

@dataclass
class AppSettingsResponseElement(DataHolderBase):
    """Class for Site Request Response from OpenApi"""
    uuid:       str
    key:        str
    value_type: str
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
        if setting.int_value != None:
            value = setting.int_value
            value_type = "int"
        elif setting.str_value != None:
            value = setting.str_value
            value_type = "string"
        elif setting.float_value != None:
            value = float_value
            value_type = "float"
        elif setting.date_value != None:
            value = date_value
            value_type = "date"
        elif setting.time_value != None:
            value = time_value
            value_type = "time"

        settings.append(
            AppSettingsResponseElement(
                uuid                  =  str(setting.uuid),
                key                   =  setting.key,
                value_type            =  value_type,
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

    target_settings = resource_by_id(db, ApplicationSettings, settings_id)

    key = request.openapi_validated.body["key"]
    value_type = request.openapi_validated.body["value_type"]
    value = request.openapi_validated.body["value"]

    if value_type == 'int':
        try:
            value_int = int(value)
        except ValueError:
            err = {
                "exception": "ValidationError",
            }   
            response_body = []
            err["message"] = "You have to provide an int."
            response_body.append(err)
            return HTTPBadRequest(json=response_body)
            
        target_settings.key = key
        target_settings.int_value = value_int
        target_settings.str_value = None
        target_settings.float_value = None
        target_settings.date_value = None
        target_settings.time_value = None

    elif value_type == 'string':
        target_settings.key = key
        target_settings.str_value = value
        target_settings.int_value = None
        target_settings.float_value = None
        target_settings.date_value = None
        target_settings.time_value = None

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
            
        target_settings.key = key
        target_settings.float_value = value_float
        target_settings.int_value = None
        target_settings.str_value = None
        target_settings.date_value = None
        target_settings.time_value = None

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

        target_settings.key = key
        target_settings.date_value = value
        target_settings.int_value = None
        target_settings.str_value = None
        target_settings.float_value = None
        target_settings.time_value = None

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

        target_settings.key = key
        target_settings.date_value = value
        target_settings.int_value = None
        target_settings.str_value = None
        target_settings.float_value = None
        target_settings.date_value = None

    else: 
        err = {
            "exception": "ValidationError",
        }   
        response_body = []
        err["message"] = "The value type has to be one of 'int, string, float, date, time'."
        response_body.append(err)
        return HTTPBadRequest(json=response_body)

    return HTTPNoContent()