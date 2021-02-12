from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config

import datameta

import bcrypt

from datameta.models import User

def hash_password(pw):
    pwhash = bcrypt.hashpw(pw.encode('utf8'), bcrypt.gensalt())
    return pwhash.decode('utf8')

def check_password(pw, hashed_pw):
    expected_hash = hashed_pw.encode('utf8')
    return bcrypt.checkpw(pw.encode('utf8'), expected_hash)


USERS = {'editor': hash_password('editor'),
         'viewer': hash_password('viewer')}
GROUPS = {'editor': ['group:editors']}


def getuser(email, request):
    return request.dbsession.query(User).filter(User.email==email).one_or_none()

def getgroup(userid, request):
    if userid in USERS:
        return GROUPS.get(userid, [])

@view_config(route_name='login', renderer='../templates/login.pt')
def my_view(request):
    request.session.invalidate()
    if request.POST:
        try:
            # Obtain submitted data
            in_email = request.POST['input_email']
            in_pwd   = request.POST['input_password']

            user = getuser(in_email, request)
            if user and check_password(in_pwd, user.pwhash):
                request.session['user_uid'] = user.id
                request.session['user_gid'] = user.group.id
                request.session['user_email'] = user.email
                request.session['user_fullname'] = user.fullname
                request.session['user_groupname'] = user.group.name
                return HTTPFound(location="/home")
        except KeyError:
            return HTTPFound(location="/login")
        return {
                'fail' : True
                }
    return {}
