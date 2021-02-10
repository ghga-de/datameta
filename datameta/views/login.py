from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config

@view_config(route_name='login', renderer='../templates/login.pt')
def my_view(request):
    print(f"CALL")
    if 'form.submitted' in request.params:
        if 'login_password' not in request.params or not request.params['login_password']:
            return HTTPFound(location="/login?pw")
        print(request.params)
    return {}
