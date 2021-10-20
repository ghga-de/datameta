# Copyright 2021 Universität Tübingen, DKFZ and EMBL for the German Human Genome-Phenome Archive (GHGA)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from pyramid.config import Configurator
from pyramid_beaker import session_factory_from_settings
from pyramid.settings import asbool
import os
from . import api

from pkg_resources import get_distribution

__version__ = get_distribution('datameta').version


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    is_2fa_enabled = asbool(settings.get("datameta.tfa.enabled", False))
    tfa_otp_issuer = settings.get("datameta.tfa.otp_issuer")
    tfa_encrypt_key = settings.get("datameta.tfa.encrypt_key")

    if is_2fa_enabled and (not tfa_otp_issuer or not tfa_encrypt_key):
        raise ValueError("2fa enabled but no issuer and/or no encryption key found")

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
        config.include('.settings')
        config.scan()
    return config.make_wsgi_app()
