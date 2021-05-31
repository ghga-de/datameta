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

from typing import List, Optional
from pyramid.httpexceptions import HTTPBadRequest, HTTPForbidden

from . import resource, models


def get_error(
    base_error,
    exception_label: str,
    messages: List[str],
    fields: Optional[List[Optional[str]]] = None,
    entities: Optional[List[Optional[str]]] = None,
):
    """Generate an Error based on the base_error with a custom message
    """
    assert len(messages) > 0, "messages cannot be empty"
    assert fields is None or len(fields) == len(messages), (
        "The fields list must be of same length as messages."
    )
    assert entities is None or len(entities) == len(messages), (
        "The entities list must be of same length as messages."
    )

    response_body = []
    for idx, msg in enumerate(messages):
        err : dict = {
            "exception": exception_label,
        }
        if entities is not None and entities[idx] is not None:
            err.update(
                {
                    "entity": resource.get_identifier(entities[idx]) if isinstance(entities[idx], models.db.Base) else entities[idx]
                }
            )
        if fields is not None and fields[idx] is not None:
            err.update(
                {
                    "field": fields[idx]
                }
            )
        err["message"] = msg
        response_body.append(err)

    return base_error(json = response_body)


def get_validation_error(
    messages: List[str],
    fields: Optional[List[Optional[str]]] = None,
    entities: Optional[List[Optional[str]]] = None
) -> HTTPBadRequest:
    """Generate a Validation Error (400) with custom message
    """
    return get_error(
        base_error = HTTPBadRequest,
        exception_label = "ValidationError",
        messages = messages,
        fields = fields,
        entities = entities
    )


def get_not_modifiable_error() -> HTTPForbidden:
    """Generate a HTTPForbidden (403) error informing
    that the resource cannot be modified
    """
    return get_error(
        base_error = HTTPForbidden,
        exception_label = "ResourceNotModifiableError",
        messages = ["The resource cannot be modified"],
    )
