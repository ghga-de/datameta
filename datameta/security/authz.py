def user_is_target(user, target_user):
    return user.uuid == target_user.uuid

def has_group_rights(user, group):
    return user.site_admin or (user.group_admin and user.group.uuid == group.uuid)

def is_power_grab(user, target_user):
    return not user.site_admin and target_user.site_admin

def has_data_access(user, data_user_id, data_group_id=None, was_submitted=False):
    # if dataset was already submitted, the group must match, or the user must have site_read priviledges
    # if dataset was not yet submitted, the user must match
    return any((
        (user.site_read),
        (was_submitted and data_group_id and data_group_id == user.group_id),
        (not was_submitted and data_user_id and data_user_id == user.id)
    ))


def apikey_view(user, target_user):
    return user_is_target(user, target_user)

def apikey_deletion(user, target_user):
    return user_is_target(user, target_user)

def appsettings_view(user):
    return user.site_admin

def appsettings_update(user):
    return user.site_admin

def file_deletion(user, file_obj):
    return has_data_access(user, file_obj.user_id)

def file_update(user, file_obj):
    return has_data_access(user, file_obj.user_id)

def file_submission(user, file_obj):
    return has_data_access(user, file_obj.user_id)

def file_view(user, file_obj):
    was_submitted = (
        file_obj.content_uploaded and 
        file_obj.metadatumrecord and  
        file_obj.metadatumrecord.metadataset.submission_id 
    )
    group_id = file_obj.metadatumrecord.metadataset.submission.group_id if was_submitted else None
    return has_data_access(user, file_obj.user_id, group_id, was_submitted=was_submitted)

def groupname_change(user):
    return user.site_admin

def group_submission_view(user, group_id):
    return any((
        (group_id in [user.group.uuid, user.group.site_id]),
        (user.site_read)
    ))

def mds_submission(user, mds_obj):
    return has_data_access(user, mds_obj.user_id)

def metadatum_update(user):
    return user.site_admin

def metadatum_creation(user):
    return user.site_admin

def mds_deletion(user, mdata_set):
    return user.id == mdata_set.user_id
    
def mds_view(user, mds_obj):
    was_submitted = bool(mds_obj.submission_id is not None)
    group_id = mds_obj.submission.group_id if was_submitted else None
    return has_data_access(user, mds_obj.user_id, data_group_id=group_id, was_submitted=was_submitted)
    
def password_change(user, target_user):
    return user_is_target(user, target_user)

def group_change(user):
    return user.site_admin

def grant_siteread(user):
    return user.site_admin

def grant_siteadmin(user, target_user):
    return user.site_admin and not user_is_target(user, target_user)

def grant_groupadmin(user, target_user):
    return has_group_rights(user, target_user.group)

def status_change(user, target_user):
    return all((
        has_group_rights(user, target_user.group),
        not is_power_grab(user, target_user),
        not user_is_target(user, target_user)
    ))

def name_change(user, target_user):
    return any((
        has_group_rights(user, target_user.group),
        user_is_target(user, target_user)
    ))