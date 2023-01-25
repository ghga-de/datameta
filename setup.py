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

import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.md')) as f:
    README = f.read()
with open(os.path.join(here, 'CHANGES.md')) as f:
    CHANGES = f.read()

requires = [
    'bcrypt',
    'psycopg2',
    'plaster_pastedeploy',
    'pandas>=1.2.2',
    'openpyxl',
    'xlrd>= 1.0.0',
    'pyramid',
    'pyramid_chameleon',
    'pyramid_beaker==0.8',
    'pylibmc==1.6.1',
    'pyramid_debugtoolbar',
    'waitress',
    'alembic',
    'pyramid_retry',
    'pyramid_tm',
    'SQLAlchemy == 1.3.*',
    'transaction',
    'zope.sqlalchemy',
    'pyramid_openapi3==0.11',
    'jsonschema<4',
    'openapi-core<0.14',
    'openapi-schema-validator==0.1.5',
    'openapi-spec-validator==0.3.1',
    'pytest >= 3.7.4',
    'dataclasses-json==0.5.2',
    "pyyaml",
    "python-json-logger",
    "gunicorn==20.0.4",
    "pyotp",
    "cryptography",
    "qrcode[pil]"
]

tests_require = [
    'WebTest >= 1.3.1',  # py3 compat
    'pytest-cov',
    "sqlalchemy_utils",
    "requests",
    "parameterized >= 0.8.1",
    "mypy",
]

setup(
    name                   = 'datameta',
    version                = '1.1.0',
    description            = 'DataMeta - submission server for data and associated metadata',
    long_description       = README + '\n\n' + CHANGES,
    author                 = 'Leon Kuchenbecker',
    author_email           = 'leon.kuchenbecker@uni-tuebingen.de',
    url                    = '',
    keywords               = 'web pyramid pylons',
    packages               = find_packages(),
    license                = 'Apache 2.0',
    include_package_data   = True,
    zip_safe               = False,
    install_requires       = requires,
    extras_require={
        'testing': tests_require,
    },
    classifiers=[
        'Programming Language :: Python',
        'License :: OSI Approved :: Apache Software License',
        'Framework :: Pyramid',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Application',
    ],
    entry_points={
        'paste.app_factory': [
            'main = datameta:main',
        ],
        'console_scripts': [
            'initialize_datameta_db=datameta.scripts.initialize_db:main',
        ],
    },
)
