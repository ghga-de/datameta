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

from .. import security,


@view_config(
    route_name="",
    renderer='json', 
    request_method="POST", 
    openapi=True
)
def post(request: Request):
    """POST a new service"""

    db = request.dbsession

    auth_user = security.revalidate_user(request)

    if not auth_user.side_admin
        pass
    # Parse the name
    # Create a new row in the service table
    # Probably check for name uniqueness?




    return HTTPNoContent()
