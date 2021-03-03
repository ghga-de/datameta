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

from dataclasses import dataclass
from pyramid.view import view_config
from pyramid.request import Request
from pyramid.httpexceptions import HTTPOk
from typing import Optional, Dict
from .. import models


# For Developers: if needed change the dataclasses to
# regular classes and supply custom __init__ functions
# (for instance if create of that class object should
# also trigger creation of the respective db model)

@dataclass
class FileBase:
    """Base class for File communication to OpenApi"""
    name: str
    file_id: str
    user_id: str
    group_id: str
    expires: Optional[str]

    def _json(self) -> dict:
        return {
                "name": self.name,
                "fileId": self.file_id,
                "userId": self.user_id,
                "groupId": self.group_id,
                "expiresAt": self.expires,
            }

@dataclass
class FileUploadResponse(FileBase):
    """FileUploadResponse container for OpenApi communication"""
    url_to_upload: str

    def __json__(self, request: Request) -> dict:
        return self._json().update(
            {
                "urlToUpload": self.url_to_upload,
            }
        )


@dataclass
class FileResponse(FileUploadResponse):
    """FileResponse container for OpenApi communication"""
    checksum: str
    content_uploaded: bool
    filesize: Optional[int] = None

    def __json__(self, request: Request) -> dict:
        
        return self._json().update(
            {
                "checkSum": self.checksum,
                "contentUploaded": self.content_uploaded,
                "fileSize": self.filesize
            }
        )


@view_config(
    route_name="files", 
    renderer='json', 
    request_method="POST", 
    openapi=True
)
def post(request: Request) -> FileUploadResponse:
    """Announce a file and get a URL for uploading it."""
    pass
    return {}


@view_config(
    route_name="files_id", 
    renderer='json', 
    request_method="GET", 
    openapi=True
)
def get_file(request: Request) -> FileResponse:
    """Get details for a file."""
    pass
    return {}
    
    
@view_config(
    route_name="files_id", 
    renderer='json', 
    request_method="PUT", 
    openapi=True
)
def update_file(request: Request) -> HTTPOk:
    """Update not-submitted file."""
    pass
    return {}

    
@view_config(
    route_name="files_id", 
    renderer='json', 
    request_method="DELETE", 
    openapi=True
)
def delete_file(request: Request) -> HTTPOk:
    """Delete not-submitted file."""
    pass
    return {}