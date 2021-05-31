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

from sqlalchemy import or_
from uuid import UUID


def get_identifier(db_obj):
    """Given a database object, return the identifying IDs as a dictionary"""
    ids = { 'uuid' : str(db_obj.uuid) }
    try:
        ids['site'] = db_obj.site_id
    except AttributeError:
        pass
    return ids


def get_identifier_or_none(db_obj):
    """Given a database object, return the identifying IDs as a dictionary or None if the object is None"""
    if db_obj is None:
        return None
    return get_identifier(db_obj)


def resource_query_by_id(db, model, idstring):
    """Returns a database query that returns an entity based on it's uuid or
    site_id as specified by idstring.

    Args:
        dbessions: A database session
        model: The model class describing the resource
        idstring: The UUID or site_id to be found

    Returns:
        Database Query object"""

    uuid_string = None
    try:
        uuid_string = UUID(idstring)
    except ValueError:
        pass

    if 'site_id' in model.__dict__:
        or_clause  = [ model.site_id == idstring ]
        or_clause += [] if uuid_string is None else [ model.uuid == uuid_string ]
        return db.query(model).filter(or_(*or_clause))
    else:
        return db.query(model).filter(model.uuid == uuid_string)


def resource_by_id(dbsession, model, idstring):
    """Tries to find a resource using the provided id. The search is initially
    performed against the resources UUID property. If that yields no match, the
    search is repeated against the resources site_id property if available.

    Args:
        dbessions: A database session
        model: The model class describing the resource
        idstring: The UUID or site_id to be found

    Returns:
        The database entity or None if no match could be found"""

    return resource_query_by_id(dbsession, model, idstring).one_or_none()
