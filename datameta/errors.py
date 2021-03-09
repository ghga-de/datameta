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
import enum
from typing import List, Optional
from pyramid.httpexceptions import HTTPBadRequest


def get_validation_error(
    messages:List[str], 
    fields:Optional[List[Optional[str]]],
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
                    "entity": entities[idx]
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
