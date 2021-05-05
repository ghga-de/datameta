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
from pyramid.httpexceptions import HTTPNoContent, HTTPUnauthorized
from sqlalchemy.exc import IntegrityError

from .. import security, errors
from ..security import authz
from ..models import Service, ServiceExecution



@view_config(
    route_name="services",
    renderer='json', 
    request_method="POST", 
    openapi=True
)
def post(request: Request):
    """POST a new service"""

    name = request.openapi_validated.body.get("name")


    auth_user = security.revalidate_user(request)

    # Check if the user is authorized to create a service
    if not authz.create_service(auth_user):
        raise HTTPUnauthorized

    db = request.dbsession

    # Try to create a new service, catch Integrity Error, if a service with that name already exists
    try:
        service = Service(name = name)
        db.add(service)
        db.flush()
    except IntegrityError:
        raise errors.get_validation_error(["A service with that name already exists."])    

    return HTTPNoContent()
