import pytest
import mock

import ckan.model as model
import ckan.plugins.toolkit as tk
import ckan.tests.factories as factories
import ckanext.hdx_theme.tests.hdx_test_base as hdx_test_base
from ckanext.hdx_org_group.helpers.static_lists import ORGANIZATION_TYPE_LIST

config = tk.config
NotAuthorized = tk.NotAuthorized
_get_action = tk.get_action


class TestQuarantineInResource(hdx_test_base.HdxBaseTest):
    EDITOR_USER = 'editor_user'
    ADMIN_USER = 'admin_user'
    SYSADMIN_USER = 'testsysadmin'
    PACKAGE_ID = 'test_dataset_4_quarantine'
    RESOURCE_ID = None

    @classmethod
    def setup_class(cls):
        super(TestQuarantineInResource, cls).setup_class()

        factories.User(name=cls.EDITOR_USER, email='quarantine_user@hdx.hdxtest.org')
        factories.User(name=cls.ADMIN_USER, email='admin_user@hdx.hdxtest.org')

        factories.Organization(
            name='org_name_4_quarantine',
            title='ORG NAME FOR QUARANTINE',
            users=[
                {'name': cls.EDITOR_USER, 'capacity': 'editor'},
                {'name': cls.ADMIN_USER, 'capacity': 'admin'},
            ],
            hdx_org_type=ORGANIZATION_TYPE_LIST[0][1],
            org_url='https://hdx.hdxtest.org/'
        )

        package = {
            'package_creator': 'test function',
            'private': False,
            'dataset_date': '[1960-01-01 TO 2012-12-31]',
            'caveats': 'These are the caveats',
            'license_other': 'TEST OTHER LICENSE',
            'methodology': 'This is a test methodology',
            'dataset_source': 'Test data',
            'license_id': 'hdx-other',
            'name': cls.PACKAGE_ID,
            'notes': 'This is a test dataset',
            'title': 'Test Dataset for Quarantine',
            'owner_org': 'org_name_4_quarantine',
            'groups': [{'name': 'roger'}],
            'resources': [
                {
                    'package_id': 'test_private_dataset_1',
                    'url': config.get('ckan.site_url', '') + '/storage/f/test_folder/hdx_test.csv',
                    'resource_type': 'file.upload',
                    'format': 'CSV',
                    'name': 'hdx_test.csv'
                }
            ]
        }
        context = {'model': model, 'session': model.Session, 'user': cls.EDITOR_USER}
        dataset_dict = _get_action('package_create')(context, package)
        cls.RESOURCE_ID = dataset_dict['resources'][0]['id']

    @staticmethod
    def __hdx_qa_resource_patch(package_id, resource_id, key, new_value, username):
        _get_action('hdx_qa_resource_patch')({'model': model, 'session': model.Session, 'user': username},
                                             {'id': resource_id, key: new_value})
        return _get_action('package_show')({}, {'id': package_id})

    @mock.patch('ckanext.hdx_package.actions.patch.tag_s3_version_by_resource_id')
    def test_quarantine_add_resource(self, tag_s3_mock):
        package_dict = self.__hdx_qa_resource_patch(self.PACKAGE_ID, self.RESOURCE_ID, 'in_quarantine', True,
                                                    self.SYSADMIN_USER)

        assert package_dict and package_dict.get('resources')[0].get('in_quarantine') is True

    @mock.patch('ckanext.hdx_package.actions.patch.tag_s3_version_by_resource_id')
    def test_quarantine_remove_resource(self, tag_s3_mock):
        package_dict = self.__hdx_qa_resource_patch(self.PACKAGE_ID, self.RESOURCE_ID, 'in_quarantine', False,
                                                    self.SYSADMIN_USER)

        assert package_dict and (
            not package_dict.get('resources')[0].get('in_quarantine') or package_dict.get('resources')[0].get(
            'in_quarantine') is False)

    @mock.patch('ckanext.hdx_package.actions.patch.tag_s3_version_by_resource_id')
    def test_quarantine_editor_raises_auth_error(self, tag_s3_mock):
        try:
            self.__hdx_qa_resource_patch(self.PACKAGE_ID, self.RESOURCE_ID, 'in_quarantine', True,
                                         self.EDITOR_USER)
            assert False
        except NotAuthorized as e:
            assert True, 'Only sysadmins can change the QA script related flags'

    @mock.patch('ckanext.hdx_package.actions.patch.tag_s3_version_by_resource_id')
    def test_quarantine_admin_raises_auth_error(self, tag_s3_mock):
        try:
            self.__hdx_qa_resource_patch(self.PACKAGE_ID, self.RESOURCE_ID, 'in_quarantine', True,
                                         self.ADMIN_USER)
            assert False
        except NotAuthorized as e:
            assert True, 'Only sysadmins can change the QA script related flags'
