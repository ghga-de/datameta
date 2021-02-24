from pyramid.config import Configurator

def includeme(config: Configurator) -> None:
    """Pyramid knob."""
    config.add_route("metadatasets", "/api/metadatasets")
    config.add_route("api_login", "/api/login")
