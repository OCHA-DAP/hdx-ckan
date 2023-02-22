import pytest
import mock

import ckan.tests.factories as factories
import ckan.model as model
import ckan.plugins.toolkit as tk

import ckanext.hdx_theme.tests.hdx_test_base as hdx_test_base

from ckanext.hdx_org_group.helpers.static_lists import ORGANIZATION_TYPE_LIST

config = tk.config
NotAuthorized = tk.NotAuthorized


class TestMicrodataInQuarantineMetafields(hdx_test_base.HdxBaseTest):
    NORMAL_USER = 'quarantine_user'
    SYSADMIN_USER = 'testsysadmin'
    PACKAGE_ID = 'test_dataset_1'

    # PACKAGE_ID = 'test_dataset_1_microdata'

    @classmethod
    def _get_action(cls, action_name):
        return tk.get_action(action_name)

    @classmethod
    def setup_class(cls):
        super(TestMicrodataInQuarantineMetafields, cls).setup_class()
        factories.User(name=cls.NORMAL_USER, email='quarantine_user@hdx.hdxtest.org')
        factories.Organization(
            name='org_name_4_quarantine',
            title='ORG NAME FOR QUARANTINE',
            users=[
                {'name': cls.NORMAL_USER, 'capacity': 'admin'},
            ],
            hdx_org_type=ORGANIZATION_TYPE_LIST[0][1],
            org_url='https://hdx.hdxtest.org/'
        )
        package = {
            "package_creator": "test function",
            "private": False,
            "dataset_date": "01/01/1960-12/31/2012",
            "caveats": "These are the caveats",
            "license_other": "TEST OTHER LICENSE",
            "methodology": "This is a test methodology",
            "dataset_source": "Test data",
            "license_id": "hdx-other",
            "name": cls.PACKAGE_ID,
            "notes": "This is a test dataset",
            "title": "Test Dataset for Quarantine",
            "owner_org": "org_name_4_quarantine",
            "groups": [{"name": "roger"}],
            "resources": [
                {
                    'package_id': 'test_private_dataset_1',
                    'url': config.get('ckan.site_url', '') + '/storage/f/test_folder/hdx_test.csv',
                    'resource_type': 'file.upload',
                    'format': 'CSV',
                    'name': 'hdx_test.csv'
                },
                {
                    'package_id': 'test_private_dataset_1',
                    'url': 'https://api.example',
                    'resource_type': 'API',
                    'format': 'CSV',
                    'name': 'hdx_api_test.csv'
                }
            ]
        }

        context = {'model': model, 'session': model.Session, 'user': cls.NORMAL_USER}
        dataset_dict = cls._get_action('package_create')(context, package)
        cls.RESOURCE_UPLOAD_ID = dataset_dict['resources'][0]['id']
        cls.RESOURCE_EXTERNAL_ID = dataset_dict['resources'][1]['id']

    @mock.patch('ckanext.hdx_package.actions.patch.tag_s3_version_by_resource_id')
    def test_normal_user_change_microdata(self, tag_s3_mock):
        context = {'model': model, 'session': model.Session}
        context_sysadmin = {'model': model, 'session': model.Session, 'user': self.SYSADMIN_USER}
        package_dict = self._get_action('package_show')(context_sysadmin, {'id': self.PACKAGE_ID})

        package_dict = self._hdx_qa_resource_patch(self.RESOURCE_UPLOAD_ID, 'in_quarantine', True, self.SYSADMIN_USER)
        package_sysadmin_dict = self._get_action('package_show')(context_sysadmin, {'id': self.PACKAGE_ID})
        assert 'url' in package_sysadmin_dict['resources'][0]
        package_user_dict = self._get_action('package_show')(context, {'id': self.PACKAGE_ID})
        assert 'url' not in package_user_dict['resources'][0]

        package_dict = self._hdx_qa_resource_patch(self.RESOURCE_EXTERNAL_ID, 'in_quarantine', True, self.SYSADMIN_USER)
        package_sysadmin_dict = self._get_action('package_show')(context_sysadmin, {'id': self.PACKAGE_ID})
        assert 'url' in package_sysadmin_dict['resources'][1]
        package_user_dict = self._get_action('package_show')(context, {'id': self.PACKAGE_ID})
        assert 'url' not in package_user_dict['resources'][1]

        assert package_dict['resources'][0]['in_quarantine'] is True
        assert package_dict['resources'][1]['in_quarantine'] is True

    def _hdx_qa_resource_patch(self, resource_id, key, new_value, username):
        try:
            self._get_action('hdx_qa_resource_patch')(
                {
                    'model': model, 'session': model.Session,
                    'user': username,
                },
                {'id': resource_id, key: new_value}
            )
        except NotAuthorized as e:
            pass
        return self._get_action('package_show')({}, {'id': self.PACKAGE_ID})
