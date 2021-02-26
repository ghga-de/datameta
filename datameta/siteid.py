# Copyright (c) 2021 Universität Tübingen, Germany
# Authors: Leon Kuchenbecker <leon.kuchenbecker@uni-tuebingen.de>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from pyramid import threadlocal

import random
from collections import defaultdict

import logging
log = logging.getLogger(__name__)

# Read parameters from config file
_prefix  = defaultdict(lambda : "UNDEFINED-")
_digits  = defaultdict(lambda : 10)

for entity in ['users', 'groups', 'submissions', 'metadatasets', 'files']:
    try:
        _prefix[entity] = threadlocal.get_current_registry().settings[f'datameta.site_id_prefix.{entity}']
    except Exception as e:
        raise
        log.warning(f"Site ID prefix for {entity} not found in configuration file ({e}).")
    try:
        _digits[entity] = int(threadlocal.get_current_registry().settings[f'datameta.site_id_digits.{entity}'])
    except Exception as e:
        raise
        log.warning(f"Site ID digits for {entity} not found in configuration file ({e}).")

def generate(request, BaseClass):
    """Generates a new site ID for the specified database entity"""
    digits = _digits[BaseClass.__tablename__]
    prefix = _prefix[BaseClass.__tablename__]
    for _ in range(10):
        new_id = prefix + str(random.randint(0, pow(10, digits))).rjust(digits, "0")
        if request.dbsession.query(BaseClass).filter(BaseClass.site_id==new_id).first():
            log.warning(f"Site ID collision for {BaseClass.__tablename__}. Your ID space may be saturating.")
        else:
            return new_id
