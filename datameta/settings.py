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

import datetime
import pkgutil
import yaml
from typing import List

import transaction
from .models import ApplicationSetting, get_engine, get_tm_session, get_session_factory

import logging
log = logging.getLogger(__name__)


def get_setting_value_type(setting):
    """Returns the type of the setting as the first value field that contains a
    value"""
    value_type = None

    if setting.int_value is not None:
        value = setting.int_value
        value_type = "int"
    elif setting.str_value is not None:
        value = setting.str_value
        value_type = "string"
    elif setting.float_value is not None:
        value = setting.float_value
        value_type = "float"
    elif setting.date_value is not None:
        value = setting.date_value
        value_type = "date"
    elif setting.time_value is not None:
        value = setting.time_value
        value_type = "time"

    return value, value_type


def get_setting(db, name):
    """Given a setting name, obtains the corresponding setting from the
    database and returns the value. The return type varies. Returns `None` if
    the setting couldn't be found or no value was set."""
    setting = db.query(ApplicationSetting).filter(ApplicationSetting.key == name).one_or_none()
    if not setting:
        return None
    elif setting.int_value is not None:
        return setting.int_value
    elif setting.str_value is not None:
        return setting.str_value
    elif setting.float_value is not None:
        return setting.float_value
    elif setting.date_value is not None:
        return setting.date_value
    elif setting.time_value is not None:
        return setting.time_value
    return None


def get_settings_startswith(
    db,
    prefix: str,
) -> List[str]:
    """Return all appsettings which starts with given prefix."""
    settings = db.query(ApplicationSetting).filter(ApplicationSetting.key.startswith(prefix)).all()
    return [setting.key for setting in settings]


class SettingUpdateError(RuntimeError):
    pass


VALUE_CASTS = {
    "int": {
        "function": int,
        "error_msg": "You have to provide an integer.",
        "target": "int_value"
    },
    "string": {
        "function": lambda value: value,
        "error_msg": "",
        "target": "str_value"
    },
    "float": {
        "function": float,
        "error_msg": "You have to provide an integer.",
        "target": "float_value"
    },
    "date": {
        "function": lambda value: datetime.datetime.strptime(value, "%Y-%m-%d"),
        "error_msg": "The date value has to specified in the form '%Y-%m-%d'.",
        "target": "date_value"
    },
    "time": {
        "function": lambda value: datetime.datetime.strptime(value, "%H:%M:%S"),
        "error_msg": "The time value has to specified in the form '%H:%M:%S'.",
        "target": "time_value"
    }
}


def set_setting(db, name, value):

    target_setting = db.query(ApplicationSetting).filter(ApplicationSetting.key == name).one_or_none()
    _, value_type = get_setting_value_type(target_setting)

    cast_params = VALUE_CASTS.get(value_type)

    if cast_params is not None:

        try:
            casted_value = cast_params["function"](value)
        except ValueError:
            raise SettingUpdateError(cast_params["error_msg"])

        setattr(target_setting, cast_params["target"], casted_value)

    return None


def includeme(config):
    """Initializes the default values for applications settings"""
    # Load the app setting defaults from the packaged yaml file
    defaults = yaml.safe_load(pkgutil.get_data(__name__, "defaults/appsettings.yaml"))
    settings = config.get_settings()
    session_factory = get_session_factory(get_engine(settings))
    with transaction.manager:
        db = get_tm_session(session_factory, transaction.manager)
        existing = [ setting.key for setting in db.query(ApplicationSetting) ]
        for key, value in defaults.items():
            if key not in existing:
                db.add(ApplicationSetting(key=key, **value))
                log.info("No application setting found, inserting default value", extra={"key": key})
