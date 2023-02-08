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

from typing import Dict
from ..models import MetaDatum, User


def is_own_group(user, group):
    return user.group.id == group.id


def user_is_target(user, target_user):
    return user.id == target_user.id


def has_group_rights(user, group):
    return user.site_admin or (user.group_admin and is_own_group(user, group))


def is_power_grab(user, target_user):
    return not user.site_admin and target_user.site_admin


def can_site_read(user):
    return user.site_admin or user.site_read


def view_user(user, target_user):
    # Regular users shall only be able to request their own user and otherwise receive a 404.
    # group_admin users shall be able to request information about all users in their group.
    # site_read (!) and site_admin users shall be able to retrieve information about all users.
    return any((
        user_is_target(user, target_user),
        has_group_rights(user, target_user.group),
        can_site_read(user)
    ))


def view_group(user, group):
    return any((
        is_own_group(user, group),  # i assume, a 'normal' user can query their group's details regardless of group_admin status?
        can_site_read(user)
    ))


def has_data_access(user, data_user_id, data_group_id=None, was_submitted=False):
    # if dataset was already submitted, the group must match, or the user must have site_read privileges
    # if dataset was not yet submitted, the user must match
    return any((
        (was_submitted and (user.site_read or data_group_id == user.group_id)),
        (not was_submitted and data_user_id == user.id)
    ))


def view_apikey(user, target_user):
    return user_is_target(user, target_user)


def delete_apikey(user, target_user):
    return user_is_target(user, target_user)


def delete_totp_secret(user):
    return user.site_admin


def view_appsettings(user):
    return user.site_admin


def update_appsettings(user):
    return user.site_admin


def submit_file(user, file_obj):
    return has_data_access(user, file_obj.user_id)


def view_file(user, file_obj):
    was_submitted = (
        file_obj.content_uploaded
        and file_obj.metadatumrecord
        and file_obj.metadatumrecord.metadataset.submission_id
    )
    group_id = file_obj.metadatumrecord.metadataset.submission.group_id if was_submitted else None
    return has_data_access(user, file_obj.user_id, group_id, was_submitted=was_submitted)


def update_group_name(user):
    return user.site_admin


def view_group_submissions(user, group_id):
    return any((
        group_id in [user.group.uuid, user.group.site_id],
        user.site_read
    ))


def update_metadatum(user):
    return user.site_admin


def create_metadatum(user):
    return user.site_admin


def get_readable_metadata(metadata: Dict[str, MetaDatum], user: User) -> Dict[str, MetaDatum]:
    """Identify metadata for which the specified user has permission to read
    corresponding records"""
    # Site-read users can read all metadata
    if user.site_read:
        return metadata
    # Non-site-read users can only read non-service metadata, even for their
    # own submissions
    return { mdat_name : mdatum for mdat_name, mdatum in metadata.items() if mdatum.service is None }


def submit_mset(user, mds_obj):
    return has_data_access(user, mds_obj.user_id)


def delete_mset(user, mdata_set):
    return user.id == mdata_set.user_id


def view_mset_any(user):
    return user.site_read


def view_mset(user, mds_obj):
    was_submitted = bool(mds_obj.submission_id is not None)
    group_id = mds_obj.submission.group_id if was_submitted else None
    return has_data_access(user, mds_obj.user_id, data_group_id=group_id, was_submitted=was_submitted)


def update_user_password(user, target_user):
    return user_is_target(user, target_user)


def update_user_group(user):
    return user.site_admin


def update_user_siteread(user):
    return user.site_admin


def update_user_siteadmin(user, target_user):
    return user.site_admin and not user_is_target(user, target_user)


def update_user_groupadmin(user, target_user):
    return has_group_rights(user, target_user.group)


def update_user_status(user, target_user):
    return all((
        has_group_rights(user, target_user.group),
        not is_power_grab(user, target_user),
        not user_is_target(user, target_user)
    ))


def update_user_name(user, target_user):
    return any((
        has_group_rights(user, target_user.group),
        user_is_target(user, target_user)
    ))


def view_restricted_user_info(user, target_user):
    return has_group_rights(user, target_user.group)


def create_service(user):
    return user.site_admin


def update_service(user):
    return user.site_admin


def view_services(user):
    return user.site_admin


def execute_service(user, service):
    return user.id in (service_user.id for service_user in service.users)
