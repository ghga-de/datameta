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

import pandas as pd
import pandas.api.types as pdtypes
import datetime

import logging
log = logging.getLogger(__name__)


class SampleSheetReadError(RuntimeError):
    pass

# HANDLING OF DATES, TIMES AND DATEIMTES
#
# All dates, times and datetimes will be stored as ISO string representations
# of datetimes in the database. dates and times will be combined with the
# minimum value counterparts to form a valid datetime, i.e. midnight for time
# and 0001-01-01 for date.
#
# The `datetimefmt` string provided in the application config is used to parse
# dates / times / datetimes from text-based sample sheet submissions (TSV, CSV)
# or when Excel files are submitted but the corresponding column is of type
# "text" rather than datetime.


def strptime_iso_or_empty(s, datetimefmt):
    try:
        return datetime.datetime.strptime(s, datetimefmt).isoformat()
    except (ValueError, TypeError):
        return ""


def datetime_iso_or_empty(x):
    try:
        return "" if pd.isna(x) else x.isoformat()
    except Exception as e:
        log.error("Failed to convert datetime.", extra={"error": e})
        return ""


def to_str(x):
    """Converts to str unless pd.isna() is true, then converts to an empty string"""
    return "" if pd.isna(x) else str(x)


def string_conversion_dates(series, datetimefmt):
    """Converts a series of dates to ISO format strings. The dates can either
    be provided as datetime objects or will otherwise be casted to `str` and
    parsed using the provided datetime format string.
    """
    if pdtypes.is_datetime64_dtype(series):
        return series.map(datetime_iso_or_empty)
    return series.map(lambda x : strptime_iso_or_empty(x, datetimefmt))


def string_conversion(data, metadata):
    """Converts all columns of the provided sample sheet to strings.
    """
    for mdat in metadata:
        if mdat.datetimefmt is not None:
            data[mdat.name] = string_conversion_dates(data[mdat.name], mdat.datetimefmt).fillna("")
        else:
            data[mdat.name] = data[mdat.name].map(to_str)
