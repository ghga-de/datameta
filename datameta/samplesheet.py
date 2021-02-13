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

import pandas as pd

from datameta.models import MetaDatum, MetaDatumRecord, MetaDataSet

class SampleSheetColumnsIncompleteError(RuntimeError):

    @property
    def columns(self):
        return self.args[0]


def import_samplesheet(request, file_like_obj, user_id, group_id):
    # Try to read the sample sheet
    data = pd.read_excel(file_like_obj)

    # Query column names that we expect to see in the sample sheet
    metadata         = [ datum for datum in request.dbsession.query(MetaDatum).all() ]
    metadata_names   = [ datum.name for datum in metadata ]

    missing_columns  = [ metadata_name for metadata_name in metadata_names if metadata_name not in data.columns ]
    if missing_columns:
        raise SampleSheetColumnsIncompleteError(missing_columns)

    # Import the provided data
    sets = [
            # Create one MetaDataSet per row of the sample sheet
            MetaDataSet(
                user_id = user_id,
                group_id = group_id,
                metadatumrecords = [
                    # Create one MetaDatumRecord for each value in the row
                    MetaDatumRecord(
                        metadatum = metadatum,
                        value = str(row[metadatum.name])
                        )
                    for metadatum in metadata
                    ]
                )
            for _, row in data.iterrows()
            ]
    request.dbsession.add_all(sets)
