# Copyright 2021 Universität Tübingen
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

import enum
from typing import List, Optional
from pyramid.httpexceptions import HTTPBadRequest

from . import resource, models

def get_validation_error(
    messages:List[str],
    fields:Optional[List[Optional[str]]]=None,
    entities:Optional[List[Optional[str]]]=None
) -> HTTPBadRequest:
    """Generate a Validation Error (400) with custom messages
    """
    assert len(messages)>0, "messages cannot be empty"
    assert fields is None or len(fields)==len(messages), (
        "The fields list must be of same length as messages."
    )
    assert entities is None or len(entities)==len(messages), (
        "The entities list must be of same length as messages."
    )

    response_body = []
    for idx, msg in enumerate(messages):
        err = {
            "exception": "ValidationError",
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

    return HTTPBadRequest(json=response_body)
