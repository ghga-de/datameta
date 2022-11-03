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
from pyramid.view import view_config
from pyramid.request import Request
from pyramid.httpexceptions import HTTPFound

from dataclasses import dataclass
from dataclasses_json import dataclass_json, LetterCase
import os
import yaml

openapi_spec_path = os.path.join(os.path.dirname(__file__), "openapi.yaml")
# read base url from openapi.yaml:
with open(openapi_spec_path, "r") as spec_file:
    openapi_spec = yaml.safe_load(spec_file)
base_url = openapi_spec["servers"][0]["url"]
api_version = openapi_spec["info"]["version"]


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class DataHolderBase:
    """Base class for data classes intended to be used as API response bodies"""
    def __json__(self, request):
        return self.to_dict()


def includeme(config: Configurator) -> None:
    """Pyramid knob."""
    config.add_route("api", "/api")
    config.add_route("server", base_url + "/server")
    config.add_route("apikeys", base_url + "/keys")
    config.add_route("apikeys_id", base_url + "/keys/{id}")
    config.add_route("user_id_keys", base_url + "/users/{id}/keys")
    config.add_route("SetUserPassword", base_url + "/users/{id}/password")
    config.add_route("totp_secret_id", base_url + "/users/{id}/totp-secret")
    config.add_route("rpc_whoami", base_url + "/rpc/whoami")
    config.add_route("user_id", base_url + "/users/{id}")
    config.add_route("metadata", base_url + "/metadata")
    config.add_route("metadata_id", base_url + "/metadata/{id}")
    config.add_route("metadatasets", base_url + "/metadatasets")
    config.add_route("metadatasets_id", base_url + "/metadatasets/{id}")
    config.add_route("appsettings", base_url + "/appsettings")
    config.add_route("appsettings_id", base_url + "/appsettings/{id}")
    config.add_route("files", base_url + "/files")
    config.add_route("files_id", base_url + "/files/{id}")
    config.add_route("submissions", base_url + "/submissions")
    config.add_route("presubvalidation", base_url + "/presubvalidation")
    config.add_route("groups_id_submissions", base_url + "/groups/{id}/submissions")
    config.add_route("groups_id", base_url + "/groups/{id}")
    config.add_route("rpc_delete_files", base_url + "/rpc/delete-files")
    config.add_route("rpc_delete_metadatasets", base_url + "/rpc/delete-metadatasets")
    config.add_route("rpc_get_file_url", base_url + "/rpc/get-file-url/{id}")
    config.add_route('register_submit', base_url + "/registrations")
    config.add_route("register_settings", base_url + "/registrationsettings")
    config.add_route("services", base_url + "/services")
    config.add_route("services_id", base_url + "/services/{id}")
    config.add_route("service_execution", base_url + "/service-execution/{serviceId}/{metadatasetId}")

    # Endpoint outside of openapi
    config.add_route("upload", base_url + "/upload/{id}")
    config.add_route("download_by_token", base_url + "/download/{token}")


@view_config(
    route_name="api",
    renderer='json',
    request_method="GET",
)
def get(request: Request):
    return HTTPFound(base_url)
