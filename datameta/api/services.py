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
from pyramid.httpexceptions import HTTPNotFound, HTTPForbidden
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload
from dataclasses import dataclass
from typing import List

from . import DataHolderBase
from .. import security, resource, siteid
from ..errors import get_validation_error
from ..security import authz
from ..models import Service, User
from ..resource import get_identifier, resource_by_id


@dataclass
class ServiceResponse(DataHolderBase):
    id: dict
    name: str
    user_ids: list


@view_config(
    route_name="services",
    renderer='json',
    request_method="POST",
    openapi=True
)
def post(request: Request) -> ServiceResponse:
    """POST a new service"""
    # Revalidate User
    auth_user = security.revalidate_user(request)

    # Check if the user is authorized to create a service
    if not authz.create_service(auth_user):
        raise HTTPForbidden()

    name = request.openapi_validated.body.get("name")

    db = request.dbsession

    # Try to create a new service, catch Integrity Error, if a service with that name already exists
    try:
        service = Service(
            name = name,
            site_id = siteid.generate(request, Service))
        db.add(service)
        db.flush()
    except IntegrityError:
        raise get_validation_error(["A service with that name already exists."])

    # Return for the new service the ID, name and all associated Users

    users = []
    for user in service.users:
        users.append(get_identifier(user))

    return ServiceResponse(
        id = resource.get_identifier(service),
        name = service.name,
        user_ids = users
    )


@view_config(
    route_name="services",
    renderer='json',
    request_method="GET",
    openapi=True
)
def get(request: Request) -> List[ServiceResponse]:
    """Get a representation of all services"""
    # Revalidate User
    auth_user = security.revalidate_user(request)

    # Check if the user is authorized to view services
    if not authz.view_services(auth_user):
        raise HTTPForbidden()

    db = request.dbsession

    # Get for all services the ID, name and all associated Users
    services = []

    for service in db.query(Service).options(joinedload(Service.users)):

        services.append(ServiceResponse(
            id = resource.get_identifier(service),
            name = service.name,
            user_ids = [resource.get_identifier(user) for user in service.users]
        ))

    return services


@view_config(
    route_name="services_id",
    renderer='json',
    request_method="PUT",
    openapi=True
)
def put(request: Request) -> ServiceResponse:
    """Update a service name and user list"""

    # Revalidate User
    auth_user = security.revalidate_user(request)

    # Check if the user is authorized to update a service
    if not authz.update_service(auth_user):
        raise HTTPForbidden()

    service_id = request.matchdict["id"]
    name = request.openapi_validated.body.get("name")
    user_ids = request.openapi_validated.body.get("userIds")

    # Check if the Service with the give id exists
    db = request.dbsession
    service = resource_by_id(db, Service, service_id)

    # Raise HTTPNotFound, if a service with the corresponding id does not exist
    if service is None:
        raise HTTPNotFound()

    # Try to update the service, catch Integrity Error, if a service with that name already exists
    try:
        # If no name was sent, don't change it
        if name is not None:
            service.name = name

        # If no userIds were sent, we don't change them
        if user_ids is not None:
            # Delete all users
            service.users = []
            messages = []

            # Add the new users
            for user_id in user_ids:
                user = resource_by_id(db, User, user_id)
                if user is None:
                    messages.append("User with id " + user_id + " does not exist.")

                service.users.append(user)

            if messages:
                raise get_validation_error(messages)

        db.flush()
    except IntegrityError:
        raise get_validation_error(["A service with that name already exists."])

    # Return for the modified service the ID, name and all associated Users

    users = []
    for user in service.users:
        users.append(get_identifier(user))

    return ServiceResponse(
        id = resource.get_identifier(service),
        name = service.name,
        user_ids = users
    )
