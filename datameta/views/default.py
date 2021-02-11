from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound

from sqlalchemy.exc import DBAPIError

from .. import models

@view_config(route_name='root')
def root_view(request):
    return HTTPFound(location="/login")
