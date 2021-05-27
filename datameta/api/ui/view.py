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

from sqlalchemy.orm import joinedload, aliased
from sqlalchemy import func, and_, or_, desc, asc

from pyramid.httpexceptions import HTTPBadRequest
from pyramid.request import Request
from pyramid.view import view_config
from dataclasses import dataclass
from typing import Optional
import shlex
import logging

from ... import security, errors, resource
from ...security import authz
from ...resource import get_identifier
from ...models import MetaDatum, MetaDataSet, MetaDatumRecord, User, Group, Submission, ServiceExecution, Service
from ...utils import get_record_from_metadataset

from ..metadata import get_all_metadata
from ..metadatasets import MetaDataSetResponse, collect_service_executions

log = logging.getLogger(__name__)


@dataclass
class ViewTableResponse(MetaDataSetResponse):
    """Data class representing the JSON response returned by POST:/api/ui/view"""
    submission_label : Optional[str] = None
    submission_datetime : Optional[str] = None  # ISO
    group_id : Optional[dict] = None
    group_name: Optional[str] = None
    user_name: Optional[str] = None


def metadata_index_to_name(db, idx):
    name = db.query(MetaDatum.name).order_by(MetaDatum.order).limit(1).offset(idx).scalar()
    if not name:
        errors.get_validation_error(["Invalid sort column index"])
    return name


@view_config(
    route_name      = "ui_view",
    renderer        = "json",
    request_method  = "POST",
)
def post(request: Request):
    """This endpoint implements the datatables API specified at
    https://datatables.net/manual/server-side
    to serve the datatables backed table in the "view data" view of the web
    front end.

    Returns:
        HTTPFound      200 - if the request could be parsed succesfully
        HTTPBadRequest 400 - if the request was invalid
    """

    auth_user   = security.revalidate_user(request)
    db          = request.dbsession

    # Parse the request as specified by the datatables API.
    try:
        # The draw number has to be returned in the response
        draw     = int(request.POST['draw'])
        # The number of records to return
        length   = int(request.POST['length'])
        # The first record to return, 0 based
        start    = int(request.POST['start'])
        # Search patterns the user entered in the search field of the table,
        # may be empty
        searches = request.POST['search[value]']
        # The column index for sorting
        sort_idx = int(request.POST['order[0][column]'])
        # The sorting direction
        sort_asc = request.POST['order[0][dir]'] == 'asc'
    except (KeyError, ValueError):
        raise HTTPBadRequest()

    direction = asc if sort_asc else desc

    MetaDataSetFilter = aliased(MetaDataSet)

    # SQL AND clauses to apply to the filter query
    and_filters = [
            # This clause joins the EXISTS subquery with the main query
            MetaDataSet.id == MetaDataSetFilter.id,
            ]

    # This clause restricts the results to submissions of the user's group
    if not authz.view_mset_any(auth_user):
        and_filters.append(Submission.group_id == auth_user.group_id)

    # Additionally, if a search pattern was requested, we create a clause
    # implementing the the search and add it to the AND clause
    if searches:
        # Split the search patterns into strings using a shell-like quoting
        # logic. We will have to JOIN MetaDatumRecord for every search term to
        # be able to AND link the search terms, thus we are also creating a
        # MetaDatumRecord table alias for every search term.
        searches = [ (search, aliased(MetaDatumRecord)) for search in shlex.split(searches) ]

        # Since every search term requires a JOIN, we limit the number of search terms
        if len(searches) > 3:
            return {
                    'draw' : draw,
                    'error' : "Please enter at most 3 search terms"
                    }

        # For every search term, we build a disjunctive clause ILIKEing the
        # search term with the metadataset and submission site_ids, the
        # submission label and the MetaDatumRecord value, using the table alias
        # that was constructed for the search term before.
        search_clauses = [ or_(*( field.ilike(f"%{search}%") for field in [ User.site_id, User.fullname, Group.site_id, Group.name, MetaDataSetFilter.site_id, Submission.site_id, Submission.label, MetaDatumRecordFilter.value ])) for search, MetaDatumRecordFilter in searches ]
        and_filters += search_clauses

    # Finally, the filter query, which will be added to the main query as a
    # subquery using EXISTS, is built
    filter_query = db.query(MetaDataSetFilter)

    # As mentioned above, we have to join MetaDatumRecord for every search term
    # that was entered. We're using the table aliases that we prepared above.
    for _, MetaDatumRecordFilter in searches:
        filter_query = filter_query.join(MetaDatumRecordFilter)

    # Beyond MetaDatumRecord, we're joining Submission and Group and adding the
    # WHERE clause by AND linking the clauses prepared above.
    filter_query = filter_query\
            .join(Submission)\
            .join(Group, Submission.group_id == Group.id)\
            .join(User, MetaDataSetFilter.user_id == User.id)\
            .filter(and_(*and_filters))

    # Query the matching metadatasets, adding the total number of records as an
    # additional column by using COUNT() as a window function. This enables us
    # to use OFFSET and LIMIT as specified in the request and yet get the total
    # number of matching records as required by datatables.
    mdatasets_base_query = db.query(MetaDataSet, func.count().over())

    mdata_name = None
    if   sort_idx == 0:  # The submission label
        mdatasets_base_query = mdatasets_base_query.join(Submission).order_by(direction(Submission.label))
    elif sort_idx == 1:  # The submission time
        mdatasets_base_query = mdatasets_base_query.join(Submission).order_by(direction(Submission.date))
    elif sort_idx == 2:  # The user full name
        mdatasets_base_query = mdatasets_base_query.join(User).order_by(direction(User.fullname))  # TODO FIX
    elif sort_idx == 3:  # The submission group name
        mdatasets_base_query = mdatasets_base_query.join(Submission).join(Group).order_by(direction(Group.site_id))  # TODO FIX
    elif sort_idx == 4:  # The metadataset site ID
        mdatasets_base_query = mdatasets_base_query.order_by(direction(MetaDataSet.site_id))
    else:  # Sorting by a metadatum value
        mdata_name = metadata_index_to_name(db, sort_idx - 5)
        # [WARNING] The following JOIN assumes that an inner join between MetaDatumRecord
        # and MetaDatum does not result in a loss of rows if the JOIN is restricted to one
        # particular MetaDatum.name. Put differently, this query requires that we always
        # store a MetaDatumRecord for every MetaDatum known, even if it is NULL.
        mdatasets_base_query = mdatasets_base_query\
                .join(MetaDatumRecord)\
                .join(MetaDatum, and_(MetaDatumRecord.metadatum_id == MetaDatum.id, MetaDatum.name == mdata_name))\
                .order_by(direction(MetaDatumRecord.value))

    # Add the EXISTS statement the query, specify the relationships that we want to JOIN for fast
    # attribute access and specify the LIMIT / OFFSET as implied by the datatable page that is
    # currently being viewed
    mdatasets_base_query = mdatasets_base_query\
            .filter(filter_query.exists())\
            .options(joinedload(MetaDataSet.submission).joinedload(Submission.group))\
            .options(joinedload(MetaDataSet.metadatumrecords).joinedload(MetaDatumRecord.metadatum))\
            .options(joinedload(MetaDataSet.metadatumrecords).joinedload(MetaDatumRecord.file))\
            .options(joinedload(MetaDataSet.user))\
            .options(joinedload(MetaDataSet.service_executions).joinedload(ServiceExecution.user))\
            .options(joinedload(MetaDataSet.service_executions).joinedload(ServiceExecution.service).joinedload(Service.target_metadata))\
            .offset(start)\
            .limit(length)\

    mdata_sets = mdatasets_base_query.all()

    # Extract the total number of matching records from the first record in the
    # window if any, otherwise assume 0
    records_filtered = 0 if not mdata_sets else mdata_sets[0][1]

    # Query the total number of records
    # Note:
    # There seems to be little benefit of providing this number to datatables.
    # If different from records_filtered, the footer shows a summary as in
    # "Showing 1 to 25 of 502 entries (filtered from 1, 800 total entries)"
    # otherwise only the first part of the message is shown. The query should
    # be rather fast, but may be a waste of resources.
    records_total = db.query(func.count(MetaDataSet.id))\
            .select_from(MetaDataSet)\
            .join(Submission)\
            .filter(Submission.group_id == auth_user.group_id)\
            .scalar()

    # Check which metadata of this metadataset the user is allowed to view
    all_metadata           = get_all_metadata(db, include_service_metadata = True)
    metadata_with_access   = authz.get_readable_metadata(all_metadata, auth_user)

    service_executions_all = [ collect_service_executions(metadata_with_access, mdata_set) for mdata_set, _ in mdata_sets ]

    # Build the 'data' response
    data = [
            ViewTableResponse(
                id                    = get_identifier(mdata_set),
                record                = get_record_from_metadataset(mdata_set, metadata_with_access),
                file_ids              = { mdrec.metadatum.name : resource.get_identifier_or_none(mdrec.file) for mdrec in mdata_set.metadatumrecords if mdrec.metadatum.isfile },
                user_id               = get_identifier(mdata_set.user),
                user_name             = mdata_set.user.fullname,
                group_id              = get_identifier(mdata_set.submission.group),
                group_name            = mdata_set.submission.group.name,
                submission_id         = get_identifier(mdata_set.submission) if mdata_set.submission else None,
                submission_datetime   = mdata_set.submission.date.isoformat(),
                submission_label      = mdata_set.submission.label,
                service_executions    = service_executions,
                )
            for (mdata_set, _), service_executions in zip(mdata_sets, service_executions_all)
            ]

    # Return the response as specified by the datatables API
    return {
            "draw"              : draw,
            "recordsTotal"      : records_total,
            "recordsFiltered"   : records_filtered,
            "data"              : data
            }
