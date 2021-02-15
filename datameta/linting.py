# Copyright (c) 2021 Leon Kuchenbecker <leon.kuchenbecker@uni-tuebingen.de>
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

from datameta.models import MetaDataSet, MetaDatum, File
from sqlalchemy import and_

from collections import Counter

def lint_pending_msets(request, user, mset_ids = None):
    """Performs linting on the pending metadatasets for a given user. Optionally filter those
    metadatasets for only those specified in the ID list."""
    db = request.dbsession

    # Query metadata fields
    mdats = db.query(MetaDatum).order_by(MetaDatum.order).all()
    mdat_names = [ mdat.name for mdat in mdats ]
    mdat_names_files = [ mdat.name for mdat in mdats if mdat.isfile ]

    # Obtain all pending metadatasets
    if mset_ids is None:
        mdatasets = db.query(MetaDataSet).filter(and_(
            MetaDataSet.submission_id==None,
            MetaDataSet.user_id==user.id,
            MetaDataSet.group_id==user.group_id))
    # Or obtain all pending metadatasets that match the specified mset ids
    else:
        mdatasets = db.query(MetaDataSet).filter(and_(
            MetaDataSet.submission_id==None,
            MetaDataSet.user_id==user.id,
            MetaDataSet.group_id==user.group_id,
            MetaDataSet.id.in_(mset_ids)))


    # Create result structure
    linting_report = { mdataset.id : [] for mdataset in mdatasets }


    # Obtain all corresponding metadata records
    mdatrecs = [ mdatrec for mdataset in mdatasets for mdatrec in mdataset.metadatumrecords ]

    # Count file name occurrences and report duplicates
    file_names        = [ mdatrec.value for mdatrec in mdatrecs if mdatrec.metadatum.isfile ]
    file_names_red    = [ file_name for file_name, count in Counter(file_names).items() if count > 1 ]
    for mdatrec in mdatrecs:
        if mdatrec.metadatum.isfile and mdatrec.value in file_names_red:
            linting_report[mdatrec.metadataset.id].append({
                'field' : mdatrec.metadatum.name,
                'type' : 'custom',
                'error' : f"Filename '{mdatrec.value}' is specified multiple times in the sample sheet."
                })

    # Check for files that have not yet been uploaded
    uploaded_files = db.query(File).filter(and_(File.user_id==user.id, File.group_id==user.group_id, File.metadatumrecord == None))
    uploaded_files = { file.name : file for file in uploaded_files }
    file_pairs = []
    for mdatrec in mdatrecs:
        if mdatrec.metadatum.isfile and mdatrec.value not in uploaded_files.keys():
            linting_report[mdatrec.metadataset.id].append({
                'field' : mdatrec.metadatum.name,
                'type' : 'nofile',
                })
        elif mdatrec.metadatum.isfile:
            file_pairs.append((mdatrec, uploaded_files[mdatrec.value]))


    # Return those metadatasets that passed linting, the record-file associations and the linting
    # report for the failed records
    good_sets = [ mdataset for mdataset in mdatasets if not linting_report[mdataset.id] ]
    return good_sets, file_pairs, linting_report
