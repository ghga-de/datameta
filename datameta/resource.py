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

from sqlalchemy import or_
from uuid import UUID

def resource_query_by_id(db, model, idstring):
    """Returns a database query that returns an entity based on it's uuid or
    site_ide as specified by idstring.

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
        or_clause  = [ model.site_id==idstring ]
        or_clause += [] if uuid_string is None else [ model.uuid==uuid_string ]
        return db.query(model).filter(or_(*or_clause))
    else:
        return db.query(model).filter(model.uuid==uuid_string)


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

    print("DING")
    return resource_query_by_id(dbsession, model, idstring).one_or_none()
