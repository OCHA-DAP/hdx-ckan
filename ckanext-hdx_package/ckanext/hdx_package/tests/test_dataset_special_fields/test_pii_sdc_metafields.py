import pytest
import mock

import ckan.tests.factories as factories
import ckan.model as model
import ckan.plugins.toolkit as tk

import ckanext.hdx_theme.tests.hdx_test_base as hdx_test_base

from ckanext.hdx_org_group.helpers.static_lists import ORGANIZATION_TYPE_LIST
from ckanext.hdx_users.helpers.permissions import Permissions

config = tk.config
NotAuthorized = tk.NotAuthorized

analytics_sender = None


class TestPiiSdcMetafields(hdx_test_base.HdxBaseTest):

    NORMAL_USER = 'quarantine_user'
    SYSADMIN_USER = 'testsysadmin'
    PACKAGE_ID = 'test_dataset_4_quarantine'
    RESOURCE_ID = None
    DATASET_ID = None

    @classmethod
    def _get_action(cls, action_name):
        return tk.get_action(action_name)

    @classmethod
    def setup_class(cls):
        super(TestPiiSdcMetafields, cls).setup_class()
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
            "dataset_date": "[1960-01-01 TO 2012-12-31]",
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
                    'url': config.get('ckan.site_url', '') + '/storage/f/test_folder/hdx_test.csv',
                    'resource_type': 'file.upload',
                    'format': 'CSV',
                    'name': 'hdx_test.csv'
                }
            ]
        }

        context = {'model': model, 'session': model.Session, 'user': cls.NORMAL_USER}
        dataset_dict = cls._get_action('package_create')(context, package)
        cls.RESOURCE_ID = dataset_dict['resources'][0]['id']
        cls.DATASET_ID = dataset_dict['id']

    @mock.patch('ckanext.hdx_package.actions.patch.tag_s3_version_by_resource_id')
    def test_normal_user_cannot_modify_quarantine(self, tag_s3_mock):
        package_dict = self._change_resource_field_via_resource_patch(self.RESOURCE_ID, 'in_quarantine', True,
                                                                      self.SYSADMIN_USER)
        assert ('in_quarantine' not in package_dict['resources'][0] or
                package_dict['resources'][0]['in_quarantine'] is False)

        package_dict = self._hdx_qa_resource_patch(self.RESOURCE_ID, 'in_quarantine', True,
                                                                      self.SYSADMIN_USER)
        assert package_dict['resources'][0]['in_quarantine'] is True

        package_dict = self._change_resource_field_via_resource_patch(self.RESOURCE_ID, 'in_quarantine', False,
                                                                      self.NORMAL_USER)
        assert package_dict['resources'][0]['in_quarantine'] is True

        package_dict = self._hdx_qa_resource_patch(self.RESOURCE_ID, 'in_quarantine', False,
                                                                      self.NORMAL_USER)
        assert package_dict['resources'][0]['in_quarantine'] is True

        package_dict = self._change_resource_field_via_resource_patch(self.RESOURCE_ID, 'in_quarantine', False,
                                                                      self.SYSADMIN_USER)
        assert package_dict['resources'][0]['in_quarantine'] is True

        package_dict = self._hdx_qa_resource_patch(self.RESOURCE_ID, 'in_quarantine', False,
                                                                      self.SYSADMIN_USER)
        assert package_dict['resources'][0]['in_quarantine'] is False

    @mock.patch('ckanext.hdx_package.actions.patch.tag_s3_version_by_resource_id')
    def test_permissions_user_can_modify_quarantine(self, tag_s3_mock):
        PERMISSIONS_USER = 'permissions_qa_completed_user'
        factories.User(name=PERMISSIONS_USER, email=PERMISSIONS_USER + '@hdx.hdxtest.org')

        package_dict = self._hdx_mark_resource_in_quarantine(self.RESOURCE_ID, True, PERMISSIONS_USER)
        assert ('in_quarantine' not in package_dict['resources'][0] or
                package_dict['resources'][0]['in_quarantine'] is False)

        Permissions(PERMISSIONS_USER).set_permissions(
            {'model': model, 'session': model.Session, 'user': self.SYSADMIN_USER},
            [Permissions.PERMISSION_MANAGE_QA]
        )

        package_dict = self._hdx_mark_resource_in_quarantine(self.RESOURCE_ID, True, PERMISSIONS_USER)
        assert package_dict['resources'][0]['in_quarantine'] is True
        package_dict = self._hdx_mark_resource_in_quarantine(self.RESOURCE_ID, False, PERMISSIONS_USER)
        assert package_dict['resources'][0]['in_quarantine'] is False


    def _change_resource_field_via_resource_patch(self, resource_id, key, new_value, username):
        self._get_action('resource_patch')(
            {
                'model': model, 'session': model.Session,
                'user': username,
            },
            {'id': resource_id, key: new_value}
        )
        return self._get_action('package_show')({}, {'id': self.PACKAGE_ID})

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

    def _hdx_mark_resource_in_quarantine(self, resource_id, new_value, username):
        try:
            self._get_action('hdx_mark_resource_in_quarantine')(
                {
                    'model': model, 'session': model.Session,
                    'user': username,
                },
                {'id': resource_id, 'in_quarantine': new_value}
            )
        except NotAuthorized as e:
            pass
        return self._get_action('package_show')({}, {'id': self.PACKAGE_ID})

