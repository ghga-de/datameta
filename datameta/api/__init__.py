# Copyright (c) 2021 Universität Tübingen, Germany
# Authors: Leon Kuchenbecker <leon.kuchenbecker@uni-tuebingen.de>,
#          Kersten Breuer <k.breuer@dkfz.de>
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
from pyramid.config import Configurator

from dataclasses import dataclass
from dataclasses_json import dataclass_json, LetterCase
import os
import yaml

openapi_spec_path = os.path.join(os.path.dirname(__file__), "openapi.yaml")
# read base url from openapi.yaml:
with open(openapi_spec_path, "r") as spec_file:
    openapi_spec = yaml.safe_load(spec_file)
base_url = openapi_spec["servers"][0]["url"]

@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class DataHolderBase:
    """Base class for data classes intended to be used as API response bodies"""
    def __json__(self, request):
        return self.to_dict()

def includeme(config: Configurator) -> None:
    """Pyramid knob."""
    config.add_route("apikeys", base_url + "/keys")
    config.add_route("apikeys_id", base_url + "/keys/{id}")
    config.add_route("user_id_keys", base_url + "/users/{id}/keys")
    config.add_route("SetUserPassword", base_url + "/users/{id}/password")
    config.add_route("metadatasets", base_url + "/metadatasets")
    config.add_route("metadatasets_id", base_url + "/metadatasets/{id}")
    config.add_route("files", base_url + "/files")
    config.add_route("files_id", base_url + "/files/{id}")
    config.add_route("submissions", base_url + "/submissions")
    config.add_route("presubvalidation", base_url + "/presubvalidation")
    config.add_route("groups_id_submissions", base_url + "/groups/{id}/submissions")
    config.add_route("groups_id", base_url + "/groups/{id}")

    # Endpoint outside of openapi
    config.add_route("upload", base_url + "/upload/{id}")
