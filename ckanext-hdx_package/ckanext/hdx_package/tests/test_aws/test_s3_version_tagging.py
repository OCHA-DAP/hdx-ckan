import os

from werkzeug.datastructures import FileStorage

from ckanext.hdx_package.helpers.constants import S3_TAG_KEY_SENSITIVE, S3_TAG_VALUE_SENSITIVE_TRUE, \
    S3_TAG_VALUE_SENSITIVE_FALSE
from ckanext.hdx_package.tests.test_aws.hdx_s3_test_base import HDXS3TestBase


class TestS3VersionTagging(HDXS3TestBase):
    def test_s3_version_tagging(self):
        file_path = os.path.join(os.path.dirname(__file__), self.file1_name)
        resource_name = 'test_resource_from_browser.csv'
        with open(file_path, 'rb') as f:
            file_upload = FileStorage(f)
            result_create = self.app.post('/api/action/resource_create',
                                          extra_environ={
                                              'Authorization': str(self.sysadmin_user['apikey']),

                                          },
                                          data={
                                              'package_id': self.dataset1_name,
                                              'name': resource_name,
                                              'url_type': 'upload',
                                              'resource_type': 'file.upload',
                                              'upload': file_upload
                                          })
            resource_dict = result_create.json['result']

        result_quarantine_tagged = self._set_quarantine_flag_on_resource(resource_dict, 'true')
        assert result_quarantine_tagged.status_code == 200

        try:
            tag1 = self._get_resource_tag(resource_dict)
            assert tag1['Key'] == S3_TAG_KEY_SENSITIVE
            assert tag1['Value'] == S3_TAG_VALUE_SENSITIVE_TRUE
        except Exception as e:
            assert False

        result_quarantine_untagged = self._set_quarantine_flag_on_resource(resource_dict, 'false')
        assert result_quarantine_untagged.status_code == 200

        try:
            tag2 = self._get_resource_tag(resource_dict)
            assert tag2['Key'] == S3_TAG_KEY_SENSITIVE
            assert tag2['Value'] == S3_TAG_VALUE_SENSITIVE_FALSE
        except Exception as e:
            assert False

    def _set_quarantine_flag_on_resource(self, resource_dict, flag_value):
        result_quarantine = self.app.post('/api/action/hdx_qa_resource_patch',
                                          extra_environ={
                                              'Authorization': str(self.sysadmin_user['apikey']),

                                          },
                                          data={
                                              'id': resource_dict['id'],
                                              'in_quarantine': flag_value,
                                          })
        return result_quarantine

    def _get_resource_tag(self, resource_dict):
        key = 'resources/{}/{}'.format(resource_dict['id'], self.file1_name)
        tagging = self.conn.meta.client.get_object_tagging(Bucket=self.bucket_name, Key=key)
        return tagging['TagSet'][0]
