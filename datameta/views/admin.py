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

import logging
from pyramid.view import view_config

from .. import security

log = logging.getLogger(__name__)


@view_config(route_name='admin', renderer='../templates/admin.pt')
def v_admin(request):
    security.revalidate_admin(request)
    try:
        return { 'showreq' : request.GET['showreq'] }
    except KeyError:
        return { 'showreq' : '' }
