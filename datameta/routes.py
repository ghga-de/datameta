def includeme(config):
    config.add_static_view('static', 'static', cache_max_age=3600)
    config.add_route('root', '/')
    config.add_route('login', '/login')
    config.add_route('home', '/home')
    config.add_route('submit', '/submit')
    config.add_route('submit_endpoint', '/submit/endpoint')
    config.add_route('account', '/account')
    config.add_route('view', '/view')
