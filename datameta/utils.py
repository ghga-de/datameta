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

from typing import Dict, Optional
from datetime import datetime

from .models import MetaDataSet, MetaDatum, MetaDatumRecord


def formatted_mrec_value(mrec: MetaDatumRecord) -> str:
    """Returns the formatted value of a metadatum record. That is, in case the
    corresponding metadatum has a datetimefmt set, it will apply the format to
    the value of the metadatum and return the result, otherwise the value of
    the metadatum is returned unchanged.

    Arguments:
        mrec: The metadatum record
    """
    if mrec.value and mrec.metadatum.datetimefmt is not None:
        return datetime.fromisoformat(mrec.value).strftime(mrec.metadatum.datetimefmt)
    else:
        return mrec.value


def formatted_mrec_value_str(value: str, datetimefmt: str) -> str:
    """Returns the formatted value of a metadatum record. That is, in case the
    corresponding metadatum has a datetimefmt set, it will apply the format to
    the value of the metadatum and return the result, otherwise the value of
    the metadatum is returned unchanged.

    Arguments:
        value         : The metadatum record value
        datetimefmt   : The metadatum record datetimefmt
    """
    if datetimefmt is not None:
        try:
            return datetime.fromisoformat(value).strftime(datetimefmt)
        except ValueError:
            pass
    return value


def get_record_from_metadataset(mdata_set: MetaDataSet, metadata: Dict[str, MetaDatum], render = True) -> Dict[str, Optional[str]]:
    """ Construct a dict containing all records of that MetaDataSet"""
    mdata_ids = [ mdatum.id for mdatum in metadata.values() ]
    return {
            rec.metadatum.name: formatted_mrec_value(rec) if render else rec.value
            for rec in mdata_set.metadatumrecords if rec.metadatum.id in mdata_ids
            }
