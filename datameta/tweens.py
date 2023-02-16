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

import os
from pyramid.settings import aslist
from pyramid.httpexceptions import HTTPServiceUnavailable

"""Module defines tween factories for the application"""


def maintenance_mode_tween_factory(handler, registry):
    """Returns a tween that checks if the application is in maintenance mode."""

    def maintenance_mode(request):
        enabled = request.registry.settings.get('datameta.maintenance_mode.path', None)
        exclude_request_paths = aslist(request.registry.settings.get('datameta.maintenance_mode.path', []))

        if enabled:
            # If request path is excluded, return response
            if request.path in exclude_request_paths:
                response = handler(request)
                return response
            # If file exists, return response
            elif os.path.isfile(enabled):
                response = handler(request)
                return response
            # If file does not exist, return 503
            else:
                return HTTPServiceUnavailable('Maintenance Mode')
        else:
            response = handler(request)
            return response

    return maintenance_mode
