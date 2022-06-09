import pytest
import os

from werkzeug.datastructures import FileStorage

from ckanext.hdx_package.tests.test_aws.hdx_s3_test_base import HDXS3TestBase

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

    @pytest.mark.parametrize('test_item', TEST_DATA)
    def test_metadata_saved_on_create(self, test_item):
        file_path = os.path.join(os.path.dirname(__file__), self.file1_name)
        resource_name = 'test_resource_from_browser.csv'
        with open(file_path, 'rb') as f:
            file_upload = FileStorage(f)
            result = self.app.post('/api/action/resource_create',
                                   extra_environ={
                                       'Authorization': str(self.sysadmin_user['apikey']),

                                   },
                                   headers={
                                       'User-Agent': test_item['user_agent']
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
        assert test_item['autoscan'] == bool(s3obj.get('Metadata', {}).get('autoscan'))

        assert resource_dict.get('download_url').split('/download/')[0]+'/download/' == resource_dict.get('alt_url')


    @pytest.mark.parametrize('test_item', TEST_DATA)
    def test_metadata_saved_on_update(self, test_item):
        file_path = os.path.join(os.path.dirname(__file__), self.file1_name)
        with open(file_path, 'rb') as f:
            file_upload = FileStorage(f)
            result = self.app.post('/api/action/resource_update',
                                   extra_environ={
                                       'Authorization': str(self.sysadmin_user['apikey']),

                                   },
                                   headers={
                                       'User-Agent': test_item['user_agent']
                                   },
                                   data={
                                       'id': self.dataset1_dict['resources'][0]['id'],
                                       'url_type': 'upload',
                                       'resource_type': 'file.upload',
                                       'upload': file_upload,
                                       'name': 'test_resource_from_browser.csv',
                                   })
        resource_dict = result.json['result']
        s3obj = self._fetch_s3_object(resource_dict['id'], self.file1_name)
        assert test_item['autoscan'] == bool(s3obj.get('Metadata', {}).get('autoscan'))

        assert resource_dict.get('download_url').split('/download/')[0] + '/download/' == resource_dict.get('alt_url')

    @pytest.mark.parametrize('test_item', TEST_DATA)
    def test_metadata_saved_on_revise(self, test_item):
        file_path = os.path.join(os.path.dirname(__file__), self.file1_name)
        with open(file_path, 'rb') as f:
            file_upload = FileStorage(f)
            result = self.app.post('/api/action/package_revise',
                                   extra_environ={
                                       'Authorization': str(self.sysadmin_user['apikey']),

                                   },
                                   headers={
                                       'User-Agent': test_item['user_agent']
                                   },
                                   data={
                                       'match__name': self.dataset1_name,
                                       'update__resources__0__url_type': 'upload',
                                       'update__resources__0__resource_type': 'file.upload',
                                       'update__resources__0__upload': file_upload,
                                       'update__resources__0__name': 'test_resource_from_browser.csv',
                                   })
        s3obj = self._fetch_s3_object(self.dataset1_dict['resources'][0]['id'], self.file1_name)
        assert test_item['autoscan'] == bool(s3obj.get('Metadata', {}).get('autoscan'))

