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

from pyramid import threadlocal

import random
from collections import defaultdict

import logging
log = logging.getLogger(__name__)

# Read parameters from config file
_prefix  = defaultdict(lambda : "UNDEFINED-")
_digits  = defaultdict(lambda : 10)

for entity in ['users', 'groups', 'submissions', 'metadatasets', 'files', 'services']:
    try:
        _prefix[entity] = threadlocal.get_current_registry().settings[f'datameta.site_id_prefix.{entity}']
    except Exception as e:
        log.warning("Site ID prefix not found in configuration file", extra={"entity": entity, "error": e})
        raise e
    try:
        _digits[entity] = int(threadlocal.get_current_registry().settings[f'datameta.site_id_digits.{entity}'])
    except Exception as e:
        log.warning("Site ID prefix not found in configuration file", extra={"entity": entity, "error": e})
        raise e


def generate(request, BaseClass):
    """Generates a new site ID for the specified database entity"""
    digits = _digits[BaseClass.__tablename__]
    prefix = _prefix[BaseClass.__tablename__]
    for _ in range(10):
        new_id = prefix + str(random.randint(0, pow(10, digits))).rjust(digits, "0")
        if request.dbsession.query(BaseClass).filter(BaseClass.site_id == new_id).first():
            log.warning("Site ID collision, ID space may be saturating.", extra={"tablename": BaseClass.__tablename__})
        else:
            return new_id
