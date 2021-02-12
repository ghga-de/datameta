from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config

import datameta

import bcrypt

from datameta.models import User

@view_config(route_name='admin', renderer='../templates/admin.pt')
def v_admin(request):
    return {}
