def user_is_target(user, target_user):
    return user.uuid == target_user.uuid

def has_group_rights(user, group):
    return user.site_admin or (user.group_admin and user.group.uuid == group.uuid)

def is_power_grab(user, target_user):
    return not user.site_admin and target_user.site_admin

def has_data_access(user, data_user_id, data_group_id=None, was_submitted=False):
    # if dataset was already submitted, the group must match
    # if dataset was not yet submitted, the user must match
    return any((
        (was_submitted and data_group_id and data_group_id == user.group_id),
        (not was_submitted and data_user_id and data_user_id == user.id)
    ))


def is_authorized_apikey_view(user, target_user):
    return user_is_target(user, target_user)

def is_authorized_apikey_deletion(user, target_user):
    return user_is_target(user, target_user)

def is_authorized_appsettings_view(user):
    return user.site_admin

def is_authorized_appsettings_update(user):
    return user.site_admin

def is_authorized_file_deletion(user, file_obj):
    return has_data_access(user, file_obj.user_id)

def is_authorized_file_update(user, file_obj):
    return has_data_access(user, file_obj.user_id)

def is_authorized_file_submission(user, file_obj):
    return has_data_access(user, file_obj.user_id)

def is_authorized_file_view(user, file_obj):
    was_submitted = (
        file_obj.content_uploaded and 
        file_obj.metadatumrecord and  
        file_obj.metadatumrecord.metadataset.submission_id 
    )
    group_id = file_obj.metadatumrecord.metadataset.submission.group_id if was_submitted else None
    return has_data_access(user, file_obj.user_id, group_id, was_submitted=was_submitted)

def is_authorized_groupname_change(user):
    return user.site_admin

def is_authorized_group_submission_view(user, group_id):
    # Only members of a group are allowed to view its submissions (what about the site admin??)
    return group_id in [user.group.uuid, user.group.site_id]

def is_authorized_mds_submission(user, mds_obj):
    return has_data_access(user, mds_obj.user_id)

def is_authorized_metadatum_update(user):
    return user.site_admin

def is_authorized_metadatum_creation(user):
    return user.site_admin

def is_authorized_mds_deletion(user, mdata_set):
    return user.id == mdata_set.user_id
    
def is_authorized_mds_view(user, mds_obj):
    was_submitted = bool(mds_obj.submission_id is not None)
    group_id = mds_obj.submission.group_id if was_submitted else None
    return has_data_access(user, mds_obj.user_id, data_group_id=group_id, was_submitted=was_submitted)
    
def is_authorized_password_change(user, target_user):
    return user_is_target(user, target_user)

def is_authorized_group_change(user):
    return user.site_admin

def is_authorized_grant_siteadmin(user, target_user):
    return user.site_admin and not user_is_target(user, target_user)

def is_authorized_grant_groupadmin(user, target_user):
    # group admin can revoke its own group admin status?
    return has_group_rights(user, target_user.group)

def is_authorized_status_change(user, target_user):
    return all((
        has_group_rights(user, target_user.group),
        not is_power_grab(user, target_user),
        not user_is_target(user, target_user)
    ))

def is_authorized_name_change(user, target_user):
    return any((
        has_group_rights(user, target_user.group),
        user_is_target(user, target_user)
    ))