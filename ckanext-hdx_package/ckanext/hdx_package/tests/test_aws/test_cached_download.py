import mock
import six

import ckan.plugins.toolkit as tk
import ckanext.s3filestore.view as s3_view

from ckanext.s3filestore.helpers import CachedDownloadStorageHelper

config = tk.config
_get_action = tk.get_action

mocked_helper = None  # type: MockedHelper

def create_storage_helper(*args, **kwargs):
    global mocked_helper
    mocked_helper = MockedHelper(*args, **kwargs)
    return mocked_helper


class TestCachedDownload(object):

    download_folder = '/tmp'

    @classmethod
    def setup_class(cls):
        cls._change_config(config)

    @classmethod
    def _change_config(cls, test_config):
        test_config['hdx.download_with_cache.datasets'] = 'test-dataset1,test-dataset2'
        test_config['hdx.download_with_cache.folder'] = cls.download_folder

    def test_should_use_download_with_cache(self):
        assert s3_view._should_use_download_with_cache('test-dataset1')
        assert s3_view._should_use_download_with_cache('test-dataset2')
        assert not s3_view._should_use_download_with_cache('test-dataset3')

    @mock.patch('ckanext.s3filestore.view._prepare_cached_response')
    @mock.patch('ckanext.s3filestore.view._get_cached_download_storage_helper', wraps=create_storage_helper)
    def test_resource_download_with_cache(self, storage_helper_func_mock, chached_response_mock):
        chached_response_mock.return_value = None

        url1 = 'http://fake1.url.org'
        filename1 = 'filename1'
        resource_dict1 = {'id': 'id1', 'last_modified': '2018-02-14T16:01:58.230736'}

        # controller1 = MockedS3Controller()
        s3_view._resource_download_with_cache(url1, filename1, resource_dict1)
        mocked_helper1 = mocked_helper
        assert mocked_helper1.file_downloaded
        assert mocked_helper1.folder_created

        # controller1_2 = MockedS3Controller()
        s3_view._resource_download_with_cache(url1, filename1, resource_dict1)
        mocked_helper1 = mocked_helper
        assert not mocked_helper1.file_downloaded
        assert not mocked_helper1.folder_created

        url2 = 'http://fake2.url.org'
        filename2 = 'filename1'  # same filename as above
        resource_dict2 = {'id': 'id1', 'last_modified': '2019-02-14T16:01:58.230736'} # same resource that was updated

        # controller2 = MockedS3Controller()
        s3_view._resource_download_with_cache(url2, filename2, resource_dict2)
        mocked_helper1 = mocked_helper
        assert mocked_helper1.file_downloaded
        assert not mocked_helper1.folder_created


# class MockedS3Controller(S3Controller):
#     def __init__(self):
#         super(MockedS3Controller, self).__init__()
#
#     def _prepare_cached_response(self, full_file_path):
#         return None
#
#     def _get_cached_download_storage_helper(self, filename, url):
#         self.mocked_helper = MockedHelper(filename, url)
#         return self.mocked_helper


class MockedHelper(CachedDownloadStorageHelper):
    existing_folders = set()
    existing_files = set()

    def __init__(self, filename, url):
        super(MockedHelper, self).__init__(filename, url)
        self.file_downloaded = False
        self.folder_created = False

    def _folder_exists(self):
        return self.folder in self.existing_folders

    def _file_exists(self):
        return self.full_file_path in self.existing_files

    def _create_folder(self):
        self.folder_created = True
        self.existing_folders.add(self.folder)

    def _download_file(self):
        self.file_downloaded = True
        self.existing_files.add(self.full_file_path)
