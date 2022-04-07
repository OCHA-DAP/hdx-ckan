import pytest
import six
import ckan.model as model

from ckan.tests import factories

import ckanext.hdx_theme.tests.hdx_test_with_inds_and_orgs as hdx_test_with_inds_and_orgs


class TestArchived(hdx_test_with_inds_and_orgs.HDXWithIndsAndOrgsTest):

    context = {'model': model, 'session': model.Session, 'user': 'editor_user'}
    context_sysadmin = {'model': model, 'session': model.Session, 'user': 'testsysadmin'}

    @classmethod
    def setup_class(cls):
        super(TestArchived, cls).setup_class()
        factories.User(name='editor_user', email='editor_user@example.com')

        cls._get_action('organization_member_create')(cls.context_sysadmin,
                                                       {'id': 'hdx-test-org', 'username': 'editor_user',
                                                        'role': 'editor'})

    def test_archived_after_package_update(self):

        # package_dict = self._get_action('package_show')(self.context_sysadmin, {'id': 'test_private_dataset_1'})
        # resource_id = package_dict['resources'][0]['id']

        dataset_dict = self._get_action('package_patch')(self.context, {
            'id': 'test_private_dataset_1',
            'archived': True,
            'private': True
        })
        assert dataset_dict['archived'] is True
        assert dataset_dict['private'] is True
        assert dataset_dict['data_update_frequency'] == '-1'

        del dataset_dict['archived']
        dataset_dict['private'] = False
        dataset_dict['data_update_frequency'] = '7'

        dataset_dict = self._get_action('package_update')(self.context, dataset_dict)
        assert dataset_dict['private'] is False
        assert dataset_dict['archived'] is True
        assert dataset_dict['data_update_frequency'] == '-1'

        dataset_dict = self._get_action('package_patch')(self.context, {
            'id': 'test_private_dataset_1',
            'archived': False,
            'data_update_frequency': '7'
        })
        assert dataset_dict['archived'] is False
        assert dataset_dict['data_update_frequency'] == '7'


    def test_archived_after_resource_update(self):

        dataset_dict = self._get_action('package_patch')(self.context, {
            'id': 'test_private_dataset_1',
            'archived': True,
            'data_update_frequency': '7'
        })
        assert dataset_dict['archived'] is True
        assert dataset_dict['data_update_frequency'] == '-1'

        resource_dict = dataset_dict['resources'][0]

        resource_dict = self._get_action('resource_update')(self.context, resource_dict)
        dataset_dict = self._get_action('package_show')(self.context_sysadmin, {'id': 'test_private_dataset_1'})
        assert dataset_dict['archived'] is True
        assert dataset_dict['data_update_frequency'] == '-1'
