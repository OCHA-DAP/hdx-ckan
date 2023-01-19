import pytest
import six
import ckan.model as model
import ckan.plugins.toolkit as tk

from ckan.tests import factories

import ckanext.hdx_theme.tests.hdx_test_with_inds_and_orgs as hdx_test_with_inds_and_orgs

NotAuthorized = tk.NotAuthorized


class TestBrokenLinkInResource(hdx_test_with_inds_and_orgs.HDXWithIndsAndOrgsTest):
    context = {'model': model, 'session': model.Session, 'user': 'editor_user'}
    context_sysadmin = {'model': model, 'session': model.Session, 'user': 'testsysadmin'}
    context_member = {'model': model, 'session': model.Session, 'user': 'member_user'}
    context_admin = {'model': model, 'session': model.Session, 'user': 'admin_user'}

    @classmethod
    def setup_class(cls):
        super(TestBrokenLinkInResource, cls).setup_class()
        factories.User(name='editor_user', email='editor_user@example.com')
        factories.User(name='member_user', email='member_user@example.com')
        factories.User(name='admin_user', email='admin_user@example.com')

        cls._get_action('organization_member_create')(cls.context_sysadmin,
                                                      {'id': 'hdx-test-org', 'username': 'editor_user',
                                                       'role': 'editor'})
        cls._get_action('organization_member_create')(cls.context_sysadmin,
                                                      {'id': 'hdx-test-org', 'username': 'member_user',
                                                       'role': 'member'})
        cls._get_action('organization_member_create')(cls.context_sysadmin,
                                                      {'id': 'hdx-test-org', 'username': 'admin_user',
                                                       'role': 'admin'})

    def test_broken_link_reset_on_package_patch(self):
        package_dict = self._get_action('package_show')(self.context_sysadmin, {'id': 'test_private_dataset_1'})
        resource_id = package_dict['resources'][0]['id']

        new_pkg_dict = self._get_action('hdx_mark_broken_link_in_resource')(self.context_sysadmin, {'id': resource_id})
        assert new_pkg_dict.get('package').get('resources')[0].get('broken_link')

        package_dict = self._get_action('package_patch')(self.context,
                                                         {'id': 'test_private_dataset_1', 'notes': 'modified'})
        assert 'broken_link' not in package_dict['resources'][0]

    def test_broken_link_reset_on_resource_patch(self):
        package_dict = self._get_action('package_show')(self.context_sysadmin, {'id': 'test_private_dataset_1'})
        resource_id = package_dict['resources'][0]['id']

        self._get_action('hdx_mark_broken_link_in_resource')(self.context_sysadmin, {'id': resource_id})

        resource_dict = self._get_action('resource_patch')(self.context, {'id': resource_id, 'broken_link': True})
        assert 'broken_link' not in resource_dict

    def test_broken_link_valid_mark_in_resource(self):
        package_dict = self._get_action('package_show')(self.context_sysadmin, {'id': 'test_private_dataset_1'})
        resource_id = package_dict['resources'][0]['id']

        self._get_action('hdx_mark_broken_link_in_resource')(self.context_sysadmin,
                                                             {'id': resource_id, 'broken_link': True})

        pkg = self._get_action('package_show')(self.context_sysadmin, {'id': 'test_private_dataset_1'})

        assert pkg.get('resources')[0].get('broken_link') is True

    def test_broken_link_valid_unmark_in_resource(self):
        package_dict = self._get_action('package_show')(self.context_sysadmin, {'id': 'test_private_dataset_1'})
        resource_id = package_dict['resources'][0]['id']

        self._get_action('hdx_mark_broken_link_in_resource')(self.context_sysadmin,
                                                             {'id': resource_id, 'broken_link': False})

        pkg = self._get_action('package_show')(self.context_sysadmin, {'id': 'test_private_dataset_1'})

        assert pkg.get('resources')[0].get('broken_link') is False

    def test_broken_link_valid_mark_in_resource_as_admin(self):
        package_dict = self._get_action('package_show')(self.context_admin, {'id': 'test_private_dataset_1'})
        resource_id = package_dict['resources'][0]['id']
        broken_link_value = package_dict['resources'][0]['broken_link']

        self._get_action('hdx_mark_broken_link_in_resource')(self.context_admin,
                                                             {'id': resource_id, 'broken_link': not broken_link_value})

        pkg = self._get_action('package_show')(self.context_admin, {'id': 'test_private_dataset_1'})

        assert not pkg['resources'][0]['broken_link'] == broken_link_value

    def test_broken_link_member_raises_auth_error(self):
        package_dict = self._get_action('package_show')(self.context_member, {'id': 'test_private_dataset_1'})
        resource_id = package_dict['resources'][0]['id']

        try:
            self._get_action('hdx_mark_broken_link_in_resource')(self.context_member,
                                                                 {'id': resource_id, 'broken_link': False})
            assert False
        except NotAuthorized as e:
            assert True, 'A member user should NOT be allowed to update the resource broken link flag'
