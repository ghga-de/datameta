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

from .models import ApplicationSettings

def get_setting(db, key):
    return db.query(ApplicationSettings).filter(ApplicationSettings.key==key).one_or_none()

# Returns the type of the setting as the first value field that contains a value
def get_setting_value_type(setting):
    value_type = None

    if setting.int_value is not None:
        value = setting.int_value
        value_type = "int"
    elif setting.str_value is not None:
        value = setting.str_value
        value_type = "string"
    elif setting.float_value is not None:
        value = float_value
        value_type = "float"
    elif setting.date_value is not None:
        value = date_value
        value_type = "date"
    elif setting.time_value is not None:
        value = time_value
        value_type = "time"

    return value, value_type
