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

from pyramid.config import Configurator


def includeme(config: Configurator) -> None:
    """Pyramid knob."""
    config.add_route("pending", "/api/ui/pending")
    config.add_route("convert", "/api/ui/convert")
    config.add_route('admin_get', '/api/ui/admin')
    config.add_route('admin_put_request', '/api/ui/admin/request')
    config.add_route('forgot_api', '/api/ui/forgot')
    config.add_route("ui_view", "/api/ui/view")
    config.add_route("set_otp", "/api/ui/set_otp")
