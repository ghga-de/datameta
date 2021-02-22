# REST API Design

If not stated otherwise, all resources managed by the API named according to the corresponding database model.

The first draft of the API focusses on managing resources which users typically iteract with during the data submission process. This primarily includes the following resources:  
- metadatasets
- submissions

User/auth related resources (especially `users` and `groups` might follow later) for automation of adiministation might follow.

## URL definitions by resource

### metadatasets

`GET /api/metadatasets`
- get all metadatasets
- only allowed for admins (since it will return entries for all groups)

`POST /api/metadatasets`
- create new metadataset

`GET/PUT/DELETE /api/metadatasets/{metadataset_id}`
- get/update/delete metadataset


### submissions

`GET /api/submissions`
- get all submissions
- only allowed for admins (since it will return entries for all groups)

`POST /api/submissions`
- create new submission that consists of a list of metadataset IDs and a list of file IDs

`GET/PUT/DELETE /api/submissions/{submission_id}`
- get/update/delete submission


### files
Only the file entries in the database will be managed by the REST API. The actual file upload should take place by directly talking to another service like S3.

`GET /api/files`
- get all files
- only allowed for admins (since it will return entries for all groups)

`POST /api/files`
- create new file
- this will only create a new file entry in the database and for instance give back a presigned URL to S3 for upload
- the actual file content shall not be part of this request

`GET/PUT/DELETE /api/files/{file_id}`
- get/update/delete file


### groups

`GET /api/groups/{group_id}`
- get info about a group

`GET /api/groups/{group_id}/users`
- lists the user's IDs which are part of this group

`GET /api/groups/{group_id}/submissions`
- lists the submission's IDs which are part of this group


### users

`GET /api/users/{user_id}`
- get info about a user (e.g. which group he/she is part of)

`GET /api/users/{user_id}/pending_metadatasets`
- lists the pending metadatasets of that user

`GET /api/users/{user_id}/pending_files`
- lists the pending files of that user