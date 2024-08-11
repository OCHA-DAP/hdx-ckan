import pytest

import ckan.tests.factories as factories
import ckan.model as model
import ckan.plugins.toolkit as tk

import ckanext.hdx_theme.tests.hdx_test_base as hdx_test_base

from ckanext.hdx_org_group.helpers.static_lists import ORGANIZATION_TYPE_LIST
from ckanext.hdx_users.helpers.permissions import Permissions

config = tk.config
NotAuthorized = tk.NotAuthorized
ValidationError = tk.ValidationError


class TestResourceInHapiField(hdx_test_base.HdxBaseTest):
    NORMAL_USER = 'hapi_user'
    SYSADMIN_USER = 'testsysadmin'
    PACKAGE_ID = 'test_dataset_1'

    PACKAGE = {
        'package_creator': 'test function',
        'private': False,
        'dataset_date': '01/01/1960-12/31/2012',
        'caveats': 'These are the caveats',
        'license_other': 'TEST OTHER LICENSE',
        'methodology': 'This is a test methodology',
        'dataset_source': 'Test data',
        'license_id': 'hdx-other',
        'name': PACKAGE_ID,
        'notes': 'This is a test dataset',
        'title': 'Test Dataset for HAPI',
        'owner_org': 'org_name_4_hapi',
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

    @classmethod
    def _get_action(cls, action_name):
        return tk.get_action(action_name)

    @classmethod
    def setup_class(cls):
        super(TestResourceInHapiField, cls).setup_class()

        factories.User(name=cls.NORMAL_USER, email='hapi_user@hdx.hdxtest.org')

        factories.Organization(
            name='org_name_4_hapi',
            title='ORG NAME FOR HAPI',
            users=[
                {'name': cls.NORMAL_USER, 'capacity': 'admin'},
            ],
            hdx_org_type=ORGANIZATION_TYPE_LIST[0][1],
            org_url='https://hdx.hdxtest.org/'
        )

        context = {'model': model, 'session': model.Session, 'user': cls.NORMAL_USER}
        dataset_dict = cls._get_action('package_create')(context, cls.PACKAGE)
        cls.RESOURCE_UPLOAD_ID = dataset_dict['resources'][0]['id']

    def test_sysadmin_can_set_in_hapi_flag(self):
        context_sysadmin = {'model': model, 'session': model.Session, 'user': self.SYSADMIN_USER}

        self._hdx_mark_resource_in_hapi(self.RESOURCE_UPLOAD_ID, 'in_hapi', 'yes', self.SYSADMIN_USER)
        package_sysadmin_dict = self._get_action('package_show')(context_sysadmin, {'id': self.PACKAGE_ID})

        assert package_sysadmin_dict['resources'][0]['in_hapi'] == 'yes', 'sysadmins should be able to set in_hapi flag'

    def test_sysadmin_can_unset_in_hapi_flag(self):
        context_sysadmin = {'model': model, 'session': model.Session, 'user': self.SYSADMIN_USER}

        self._hdx_mark_resource_in_hapi(self.RESOURCE_UPLOAD_ID, 'in_hapi', 'no-data', self.SYSADMIN_USER)
        package_sysadmin_dict = self._get_action('package_show')(context_sysadmin, {'id': self.PACKAGE_ID})

        assert 'in_hapi' not in package_sysadmin_dict['resources'][0], 'sysadmins should be able to unset in_hapi flag'

    def test_sysadmin_cannot_set_invalid_in_hapi_flag(self):
        context_sysadmin = {'model': model, 'session': model.Session, 'user': self.SYSADMIN_USER}

        try:
            self._hdx_mark_resource_in_hapi(self.RESOURCE_UPLOAD_ID, 'in_hapi', 'invalid-value', self.SYSADMIN_USER)
        except ValidationError as e:
            assert 'in_hapi' in e.error_dict, 'hdx_mark_resource_in_hapi should fail when using invalid values'

        package_sysadmin_dict = self._get_action('package_show')(context_sysadmin, {'id': self.PACKAGE_ID})
        assert 'in_hapi' not in package_sysadmin_dict['resources'][0], 'in_hapi flag should not be set on invalid value'

    def test_normal_user_cannot_set_in_hapi_flag(self):
        context = {'model': model, 'session': model.Session, 'user': self.NORMAL_USER}

        try:
            self._hdx_mark_resource_in_hapi(self.RESOURCE_UPLOAD_ID, 'in_hapi', 'yes', self.NORMAL_USER)
        except NotAuthorized:
            assert True

        package_user_dict = self._get_action('package_show')(context, {'id': self.PACKAGE_ID})
        assert 'in_hapi' not in package_user_dict['resources'][0], 'normal users should not be able to set in_hapi flag'

    def test_normal_user_with_permissions_can_set_in_hapi_flag(self):
        context = {'model': model, 'session': model.Session, 'user': self.NORMAL_USER}

        Permissions(self.NORMAL_USER).set_permissions(
            {'model': model, 'session': model.Session, 'user': self.SYSADMIN_USER},
            [Permissions.PERMISSION_MANAGE_IN_HAPI_FLAG]
        )

        self._hdx_mark_resource_in_hapi(self.RESOURCE_UPLOAD_ID, 'in_hapi', 'yes', self.NORMAL_USER)

        package_user_dict = self._get_action('package_show')(context, {'id': self.PACKAGE_ID})
        assert package_user_dict['resources'][0][
                   'in_hapi'] == 'yes', 'normal users with the right permission should be able to set in_hapi flag'

    def test_in_hapi_flag_persists_on_package_update(self):
        context_sysadmin = {'model': model, 'session': model.Session, 'user': self.SYSADMIN_USER}

        package_sysadmin_dict = self._get_action('package_show')(context_sysadmin, {'id': self.PACKAGE_ID})
        assert package_sysadmin_dict['resources'][0]['in_hapi'] == 'yes'

        dataset_dict_modified = self.PACKAGE
        dataset_dict_modified['notes'] = 'This is a modified dataset'
        self._get_action('package_update')(context_sysadmin, dataset_dict_modified)

        assert package_sysadmin_dict['resources'][0][
                   'in_hapi'] == 'yes', 'in_hapi flag should persist after package_update'

    def _hdx_mark_resource_in_hapi(self, resource_id, key, new_value, username):
        context = {'model': model, 'session': model.Session, 'user': username}
        data_dict = {'id': resource_id, key: new_value}

        self._get_action('hdx_mark_resource_in_hapi')(context, data_dict)
