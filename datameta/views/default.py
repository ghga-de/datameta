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
from pyramid.httpexceptions import HTTPFound

from .. import security, settings

from pyramid.events import subscriber
from pyramid.events import BeforeRender

import logging
log = logging.getLogger(__name__)


@subscriber(BeforeRender)
def add_global(event):
    def add_appsetting_with_default(appsetting_name: str, default: str) -> None:
        appsetting = settings.get_setting(event['request'].dbsession, appsetting_name)
        if appsetting is None:
            event[appsetting_name] = default
            log.error(f"Missing application settings {appsetting_name}")
        else:
            event[appsetting_name] = appsetting

    add_appsetting_with_default("logo_html", "")
    add_appsetting_with_default("legal_notice", "")


@view_config(route_name='root')
def root_view(request):
    security.revalidate_user_or_login(request)
    return HTTPFound(location="/home")
