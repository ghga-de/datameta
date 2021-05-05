"""Testing site read capabilities via API request
"""
from . import BaseIntegrationTest
from datameta.api import base_url



class SiteReadTest(BaseIntegrationTest):
    def xtest_access_staged_file(self):
        # this still throws 
        # TypeError: 'NoneType' object is not iterable
        # /usr/local/lib/python3.8/site-packages/openapi_core/unmarshalling/schemas/unmarshallers.py:149: TypeError
        file_ids = [site_id for site_id, f in self.default_files.items() if not f.submitted]
        user = self.default_users["group_z_site_read"]

        for file_id in file_ids:
            response = self.testapp.get(
                f"{base_url}/files/{file_id}",
                headers=user.auth.header,
                status=403
            )

    def test_access_staged_metadataset(self):
        mds_ids = [site_id for site_id, mds in self.default_metadatasets.items() if not mds.submitted]
        user = self.default_users["group_z_site_read"]

        for mds_id in mds_ids:
            response = self.testapp.get(
                f"{base_url}/metadatasets/{mds_id}",
                headers=user.auth.header,
                status=403
            )