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
import transaction
import json
from dataclasses import dataclass, field
import hashlib
import yaml
from importlib import import_module
from typing import Optional, List
from collections import defaultdict
from copy import deepcopy
import shutil

import datetime

from datameta.models import get_tm_session
from datameta.models.meta import Base as DatabaseModel
from datameta.models import MetaDatum, MetaDatumRecord, File
from . import holders
from ..utils import get_file_path

class FixtureNotFoundError(RuntimeError):
    pass

# get URL to test db from environment variable:
db_url = os.getenv("SQLALCHEMY_TEST_URL")
assert db_url, "Could not find environment variable \"SQLALCHEMY_TEST_URL\""
memcached_url = os.getenv("SESSION_URL")
assert memcached_url, "Could not find environment variable \"SESSION_URL\""

# read settings.json
base_dir = os.path.dirname(__file__)
default_settings_json = os.path.join(base_dir, "settings.json")
with open(default_settings_json, "r") as json_:
    default_settings = json.load(json_)
default_settings["sqlalchemy.url"] = db_url
default_settings["session.url"] = memcached_url

def datetime_from_isoformat(s:str) -> datetime.datetime:
    return datetime.datetime.fromisoformat(s)

class FixtureManager:

    def __init__(self, session_factory, storage_path):
        self.fixtures          = {}
        self.db_ids            = {}
        self.session_factory   = session_factory
        self.storage_path      = storage_path

    def _create_fixture(self, db, fixture_set:str, fixture_name:str,  fixture:dict, database_insert=True):
        """Creates a fixture based on the provided dictionary"""
        models = import_module('datameta.models')
        db_class_name = fixture['class']
        Entity = getattr(models, db_class_name)

        #
        # VALIDATION
        #
        regular_attrs = set(fixture['attributes'].keys()) if 'attributes' in fixture else set()
        ref_attrs = set(fixture['references'].keys()) if 'references' in fixture else set()
        if not regular_attrs.isdisjoint(ref_attrs):
            raise RuntimeError(f"The fixture '{fixture}' has conflicting keys specified both under 'attributes' and 'references'")

        #
        # REGULAR ATTRIBUTES
        #
        attributes = {}
        fixture_only_attributes = {}
        ref_attributes = {}
        fixture_only = fixture['fixtureOnly'] if 'fixtureOnly' in fixture else []
        for attr_name, attr_value in fixture['attributes'].items():
            # If this attribute is enlisted in 'fixtureOnly' then we just
            # carry over the value to the fixture dataclass and do nothing
            # else. Note that the value can be a more complex data
            # structure.
            if attr_name in fixture_only:
                fixture_only_attributes[attr_name] = attr_value
            elif isinstance(attr_value, dict):
                attr_dict = attr_value
                # This fixture attribute needs to be processed by a function
                if 'func' in attr_dict:
                    new_name = attr_dict['newname']
                    func_path = attr_dict['func'].split('.')
                    func_mod  = '.'.join(func_path[:-1])
                    func_name = func_path[-1]
                    func = getattr(import_module(func_mod), func_name) if func_mod else globals()[func_name]
                    attributes[new_name] = func(attr_dict['value'])
                    fixture_only_attributes[attr_name] = attr_dict['value']
                else:
                    raise RuntimeError(f"Failed to parse fixture {fixture}")
            else:
                attributes[attr_name] = attr_value

        #
        # REFERENCE ATTRIBUTES
        #
        references = fixture['references'] if 'references' in fixture else {}
        for attr_name, attr_value in references.items():
            multiple = isinstance(attr_value, list)
            references = attr_value if multiple else [ attr_value ]
            if database_insert:
                ref_objects = []
                for reference in references:
                    try:
                        ref_fixture = self.fixtures[reference['fixtureset'], reference['name']]
                    except KeyError:
                        raise RuntimeError(f"Could not find referenced fixture '{reference['fixtureset']}.{reference['name']}'. You may have to load other fixtures first.")
                    ref_fixture_id              = ref_fixture.id
                    RefEntity                   = getattr(import_module('datameta.models'), ref_fixture.__db_class__)
                    ref_entity                  = db.query(RefEntity).filter(RefEntity.id==ref_fixture_id).one_or_none()
                    ref_objects.append(ref_entity)
                ref_attributes[attr_name]       = ref_objects if multiple else ref_objects[0]
            fixture_only_attributes[attr_name] = attr_value

        #
        # DATABASE INSERT AND ID CAPTURE
        #
        e = Entity(**attributes, **ref_attributes)
        if database_insert:
            db.add(e)
            db.flush()
            # Add the identifiers to the fixture
            attributes['id'] = e.id
            attributes['uuid'] = e.uuid
        else:
            attributes['id'] = None
            attributes['uuid'] = None

        Fixture = getattr(globals()['holders'], db_class_name+'Fixture')
        self.fixtures[fixture_set, fixture_name] = Fixture(__db_class__ = db_class_name, **attributes, **fixture_only_attributes)

    def load_fixtureset(self, fixture_set:str, database_insert=True):
        """Load a fixture set. The name corresponds to the basename of the fixture yaml file"""
        with open(os.path.join(base_dir, f"{fixture_set}.yaml"), 'r') as infile:
            fixtures = yaml.safe_load(infile)
        with transaction.manager:
            db = get_tm_session(self.session_factory, transaction.manager)
            for fixture_name, fixture in fixtures.items():
                self._create_fixture(db, fixture_set, fixture_name, fixture, database_insert=database_insert)

    def get_fixtureset(self, fixture_set:str) -> dict:
        res =  { 
                fixture_name : fixture
                for (fixture_set_, fixture_name), fixture in self.fixtures.items() if fixture_set_==fixture_set
                }
        if not res:
            raise FixtureNotFoundError(f"Could not find fixture set '{fixture_set}'. The fixture set was not loaded or is empty.")
        return res

    def get_fixture(self, fixtureset:str, name:str) -> dict:
        """Returns the fixture object corresponding to a fixture given the
        fixture set name and the fixture name."""
        try:
            return self.fixtures[fixtureset, name]
        except KeyError:
            raise FixtureNotFoundError(f"Could not find fixture '{name}' in '{fixtureset}'. The fixture may not exist or the fixture set '{fixtureset}' was not loaded.")

    def get_fixture_db(self, fixture_set:str, fixture_name:str, *query_options) -> DatabaseModel:
        """Queries and returns the database object corresponding to a fixture
        given the fixture set name and the fixture name."""

        fixture      = self.fixtures[fixture_set, fixture_name]
        fixture_id   = fixture.id
        Entity       = getattr(import_module('datameta.models'), fixture.__db_class__)

        with transaction.manager:
            db = get_tm_session(self.session_factory, transaction.manager, expire_on_commit=False)
            return db.query(Entity).filter(Entity.id==fixture_id).options(*query_options).one_or_none()

    def populate_metadatasets(self):
        with transaction.manager:
            db = get_tm_session(self.session_factory, transaction.manager, expire_on_commit=False)
            # Collect the metadata definitions from the database and map their
            # names to the corresponding primary key
            metadata = { mdat.name : mdat for mdat in db.query(MetaDatum) }
            files    = { file.name : file for file in db.query(File) }
            for (fixture_set, fixture_name), fixture in self.fixtures.items():
                # Check if the fixture is a metadataset and if it was loaded
                # with database insert (id is set)
                if fixture.__db_class__ == 'MetaDataSet' and fixture.id is not None:
                    mdat_records = { mdat_name : MetaDatumRecord(
                        metadatum_id     = metadata[mdat_name].id,
                        metadataset_id   = fixture.id,
                        value            = mdat_value
                        ) for mdat_name, mdat_value in fixture.records.items() }
                    # Link the file if submitted and the fixture was loaded with DB insert (id is set)
                    if fixture.submission is not None and fixture.id is not None:
                        for mdat_name in [ name for name, mdat in metadata.items() if mdat.isfile ]:
                            # If this metadatum was not specified in the fixture, skip it
                            if mdat_name not in mdat_records:
                                continue
                            # Otherwise, reference the file
                            rec = mdat_records[mdat_name]
                            if rec.value not in files:
                                raise RuntimeError(f"Could not populate metadataset '{fixture_name}' from fixture set '{fixture_set}': Metadataset is linked to a submission, but referenced files cannot be found. Did you load the necessary file fixtures?")
                            rec.file_id = files[rec.value].id
                    db.add_all(mdat_records.values())

    def copy_files_to_storage(self):
        with transaction.manager:
            db = get_tm_session(self.session_factory, transaction.manager, expire_on_commit=False)

            for file in db.query(File):
                storage_name =  f"{str(file.uuid)}__{file.checksum}"
                shutil.copy(get_file_path(file.name), os.path.join(self.storage_path, storage_name))
                file.storage_uri = f"file://{storage_name}"
                db.add(file)
