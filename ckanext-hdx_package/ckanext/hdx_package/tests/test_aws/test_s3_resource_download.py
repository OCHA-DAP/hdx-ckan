import pytest
import json
import os
import ckan.model as model
import ckan.plugins.toolkit as tk
from werkzeug.datastructures import FileStorage
import mock

from ckanext.hdx_package.tests.test_aws.hdx_s3_test_base import HDXS3TestBase

_get_action = tk.get_action
url_for = tk.url_for

TEST_DATA = [
    {
        'user_agent': '',
        'autoscan': False,
    },
    {
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36',
        'autoscan': True,
    },
    {
        'user_agent': 'HDXINTERNAL:HDXPythonLibrary/4.9.9-FTS',
        'autoscan': False,
    },

]


class TestS3Metadata(HDXS3TestBase):

    @mock.patch('ckanext.hdx_package.views.download_wrapper.view')
    def test_metadata_saved_on_create(self, mock_view):
        mock_view.return_value = json.dumps({'success': True})
        mock_view.download.return_value = json.dumps({'success': True})
        file_path = os.path.join(os.path.dirname(__file__), self.file1_name)
        resource_name = 'test_resource_from_browser.csv'
        with open(file_path, 'rb') as f:
            file_upload = FileStorage(f)
            result = self.app.post('/api/action/resource_create',
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
        resource_dict = result.json['result']
        s3obj = self._fetch_s3_object(resource_dict['id'], self.file1_name)
        assert resource_dict.get('download_url').split('/download/')[0] + '/download/' == resource_dict.get('alt_url')

        result = self.app.post('/api/action/resource_create',
                               extra_environ={
                                   'Authorization': str(self.sysadmin_user['apikey']),

                               },
                               data={
                                   'package_id': self.dataset1_name,
                                   'name': 'test external url',
                                   'url': 'https://centre.humdata.org',
                                   'url_type': 'api',
                                   'resource_type': 'api',
                                   'format': 'API'
                               })
        context = {'model': model, 'session': model.Session, 'user': 'testsysadmin'}
        pkg_dict = _get_action('package_show')(context, {'id': self.dataset1_name})

        result = self.app.get(url_for("hdx_download_wrapper.download_at_position", id=self.dataset1_name, n=0))
        assert '{"success": true}' in result.body

        result = self.app.get(url_for("hdx_download_wrapper.download_at_position", id=self.dataset1_name, n=1))
        assert '{"success": true}' in result.body

        result = self.app.get(url_for("hdx_download_wrapper.download_at_position", id=self.dataset1_name, n=2),
                              follow_redirects=False)
        assert 'https://centre.humdata.org' in result.body
