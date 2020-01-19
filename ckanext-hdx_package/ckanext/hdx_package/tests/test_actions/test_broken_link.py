import ckan.model as model

from ckan.tests import factories

import ckanext.hdx_theme.tests.hdx_test_with_inds_and_orgs as hdx_test_with_inds_and_orgs


class TestBrokenLinkInResource(hdx_test_with_inds_and_orgs.HDXWithIndsAndOrgsTest):

    context = {'model': model, 'session': model.Session, 'user': 'editor_user'}
    context_sysadmin = {'model': model, 'session': model.Session, 'user': 'testsysadmin'}

    @classmethod
    def setup_class(cls):
        super(TestBrokenLinkInResource, cls).setup_class()
        factories.User(name='editor_user', email='editor_user@example.com')

        cls._get_action('organization_member_create')(cls.context_sysadmin,
                                                       {'id': 'hdx-test-org', 'username': 'editor_user',
                                                        'role': 'editor'})


    def test_broken_link_reset_on_package_patch(self):

        package_dict = self._get_action('package_show')(self.context_sysadmin, {'id': 'test_private_dataset_1'})
        resource_id = package_dict['resources'][0]['id']

        resource_dict = self._get_action('hdx_mark_broken_link_in_resource')(self.context_sysadmin, {'id': resource_id})
        assert resource_dict['broken_link']

        package_dict = self._get_action('package_patch')(self.context, {'id': 'test_private_dataset_1', 'notes': 'modified'})
        assert 'broken_link' not in package_dict['resources'][0]

    def test_broken_link_reset_on_resource_patch(self):

        package_dict = self._get_action('package_show')(self.context_sysadmin, {'id': 'test_private_dataset_1'})
        resource_id = package_dict['resources'][0]['id']

        self._get_action('hdx_mark_broken_link_in_resource')(self.context_sysadmin, {'id': resource_id})

        resource_dict = self._get_action('resource_patch')(self.context, {'id': resource_id, 'broken_link': True})
        assert 'broken_link' not in resource_dict
