from pyramid.config import Configurator
from pyramid_beaker import session_factory_from_settings
import os
from . import api

def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    with Configurator(settings=settings) as config:
        # Session config
        session_factory = session_factory_from_settings(settings)
        config.set_session_factory(session_factory)

        config.include("pyramid_openapi3")
        config.pyramid_openapi3_spec(
            os.path.join(os.path.dirname(__file__), "api", "openapi.yaml")
        )
        config.pyramid_openapi3_add_explorer(api.base_url)
        config.include('.models')
        config.include('pyramid_chameleon')
        config.include('.routes')
        config.include('.api')
        config.include('.api.ui')
        config.scan()
    return config.make_wsgi_app()
