from pyramid.config import Configurator
from pyramid_beaker import session_factory_from_settings

from .views.login import getgroup

def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    with Configurator(settings=settings) as config:
        # Session config
        session_factory = session_factory_from_settings(settings)
        config.set_session_factory(session_factory)

        config.include('.models')
        config.include('pyramid_chameleon')
        config.include('.routes')
        config.scan()
    return config.make_wsgi_app()
