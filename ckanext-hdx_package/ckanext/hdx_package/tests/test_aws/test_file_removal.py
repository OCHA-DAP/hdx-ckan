import os
from werkzeug import FileStorage

import boto3 as boto3
from moto import mock_s3

import ckan.model as model
import ckan.plugins.toolkit as tk

import ckan.lib.search as search
import ckan.tests.helpers as helpers
import ckan.tests.factories as factories

from ckanext.hdx_org_group.helpers.static_lists import ORGANIZATION_TYPE_LIST

config = tk.config
_get_action = tk.get_action


class TestFileRemovalS3(object):

    m_s3 = None
    conn = None
    original_config = {}

    bucket_name = 'some-bucket-name'
    dataset1_name = 'test-file-removal-dataset-1'
    dataset2_name = 'test-file-removal-dataset-2'
    file1_name = 'data1.csv'
    file2_name = 'data2.csv'

    @classmethod
    def setup_class(cls):
        search.clear_all()
        helpers.reset_db()

        cls.original_config = config.copy()
        cls._change_config(config)

        cls.m_s3 = mock_s3()
        cls.m_s3.start()

        cls.conn = boto3.resource('s3', region_name=config['ckanext.s3filestore.region_name'])
        cls.conn.create_bucket(Bucket=cls.bucket_name)

        app = helpers._get_test_app()

        factories.Sysadmin(name='testsysadmin')
        cls._create_packages_by_user(cls.dataset1_name, 'testsysadmin')

    @classmethod
    def teardown_class(cls):
        cls.m_s3.stop()
        model.Session.remove()

        config.clear()
        config.update(cls.original_config)


    @classmethod
    def _change_config(cls, test_config):
        test_config['ckan.plugins'] += ' s3filestore'
        ## AWS S3 settings
        test_config['ckanext.s3filestore.aws_access_key_id'] = 'aws_access_key_id'
        test_config['ckanext.s3filestore.aws_secret_access_key'] = 'aws_secret_access_key'
        test_config['ckanext.s3filestore.aws_bucket_name'] = cls.bucket_name
        test_config['ckanext.s3filestore.host_name'] = 'http://s3.eu-central-1.amazonaws.com'
        test_config['ckanext.s3filestore.region_name'] = 'eu-central-1'
        test_config['ckanext.s3filestore.signature_version'] = 's3v4'
        test_config['ckanext.s3filestore.link_expires_in_seconds'] = 180

        test_config.pop('hdx.s3filestore', None)

    @classmethod
    def _create_packages_by_user(cls, pkg_id, user, create_org_and_group=True):
        if create_org_and_group:
            factories.Organization(name='test_owner_org', org_url='http://example.org/',
                                   hdx_org_type=ORGANIZATION_TYPE_LIST[0][1],
                                   users=[{'name': 'testsysadmin', 'capacity': 'admin'}]
                                   )
            factories.Group(name='test_group1')
        package = {
            "package_creator": "test function",
            "private": False,
            "dataset_date": "[1960-01-01 TO 2012-12-31]",
            "caveats": "These are the caveats",
            "license_other": "TEST OTHER LICENSE",
            "methodology": "This is a test methodology",
            "dataset_source": "Test data",
            "license_id": "hdx-other",
            "name": pkg_id,
            "notes": "This is a test dataset",
            "title": "Test Dataset for QA Completed " + pkg_id,
            "owner_org": "test_owner_org",
            "groups": [{"name": "test_group1"}],
            "maintainer": "testsysadmin",
            "data_update_frequency": "0",
            "resources": [
                {
                    'package_id': pkg_id,
                    'url': config.get('ckan.site_url', '') + '/storage/f/test_folder/hdx_test.csv',
                    'resource_type': 'file.upload',
                    'format': 'CSV',
                    'name': 'hdx_test.csv'
                }
            ]
        }

        context = {'model': model, 'session': model.Session, 'user': user}
        _get_action('package_create')(context, package)

    @classmethod
    def __resource_create_with_upload(cls, context, filename, resource_name, dataset_name):
        file_path = os.path.join(os.path.dirname(__file__), filename)
        with open(file_path) as f:
            file_upload = FileStorage(f)
            resource_dict = _get_action('resource_create')(context,
                                                           {
                                                               'package_id': dataset_name,
                                                               'name': resource_name,
                                                               'url_type': 'upload',
                                                               'resource_type': 'file.upload',
                                                               'upload': file_upload

                                                           }
                                                           )
        return resource_dict

    @classmethod
    def __resource_update_with_upload(cls, context, filename, resource_name, resource_id):
        file_path = os.path.join(os.path.dirname(__file__), filename)
        with open(file_path) as f:
            file_upload = FileStorage(f)
            resource_dict = _get_action('resource_update')(context,
                                                           {
                                                               'id': resource_id,
                                                               'name': resource_name,
                                                               'url_type': 'upload',
                                                               'resource_type': 'file.upload',
                                                               'upload': file_upload

                                                           }
                                                           )
        return resource_dict

    def test_resource_delete(self):

        context = {'model': model, 'session': model.Session, 'user': 'testsysadmin'}
        resource_dict = self.__resource_create_with_upload(context, self.file1_name, 'Test resource1.csv',
                                                           self.dataset1_name)

        resource_id = resource_dict['id']
        assert self.__file_exists(resource_id, self.file1_name)

        _get_action('resource_delete')(context, {'id': resource_id})
        assert not self.__file_exists(resource_id, self.file1_name)

    def test_resource_update(self):

        context = {'model': model, 'session': model.Session, 'user': 'testsysadmin'}
        resource_dict = self.__resource_create_with_upload(context, self.file1_name, 'Test resource1.csv',
                                                           self.dataset1_name)

        resource_id = resource_dict['id']

        resource_dict2 = self.__resource_update_with_upload(context, self.file2_name, self.file2_name, resource_id)
        assert not self.__file_exists(resource_id, self.file1_name)
        assert self.__file_exists(resource_id, self.file2_name)

        _get_action('resource_delete')(context, {'id': resource_id})
        assert not self.__file_exists(resource_id, self.file2_name)

    def test_resource_update_with_same_resource_name(self):

        context = {'model': model, 'session': model.Session, 'user': 'testsysadmin'}
        resource_dict = self.__resource_create_with_upload(context, self.file1_name, 'Test resource1.csv',
                                                           self.dataset1_name)

        resource_id = resource_dict['id']

        resource_dict2 = self.__resource_update_with_upload(context, self.file2_name, 'Test resource1.csv', resource_id)
        assert not self.__file_exists(resource_id, self.file1_name)
        assert self.__file_exists(resource_id, self.file2_name)

        _get_action('resource_delete')(context, {'id': resource_id})
        assert not self.__file_exists(resource_id, self.file2_name)

    def test_resource_update_with_same_file_name(self):

        context = {'model': model, 'session': model.Session, 'user': 'testsysadmin'}
        resource_dict = self.__resource_create_with_upload(context, self.file1_name, 'Test resource1.csv',
                                                           self.dataset1_name)

        resource_id = resource_dict['id']

        resource_dict2 = self.__resource_update_with_upload(context, self.file1_name, 'Test resource2.csv', resource_id)
        assert self.__file_exists(resource_id, self.file1_name)

        _get_action('resource_delete')(context, {'id': resource_id})
        assert not self.__file_exists(resource_id, self.file1_name)

    def test_package_purge(self):
        context = {'model': model, 'session': model.Session, 'user': 'testsysadmin'}
        self._create_packages_by_user(self.dataset2_name, 'testsysadmin', create_org_and_group=False)
        resource_dict = self.__resource_create_with_upload(context, self.file1_name, 'Test resource1.csv',
                                                           self.dataset2_name)

        resource_id = resource_dict['id']

        _get_action('hdx_dataset_purge')(context, {'id': self.dataset2_name})
        assert not self.__file_exists(resource_id, self.file1_name)

    def __file_exists(self, resource_id, file_name):
        key = 'resources/{}/{}'.format(resource_id, file_name)
        try:
            s3_obj = self.conn.Object(self.bucket_name, key).get()
            return bool(s3_obj)
        except Exception as e:
            return False
