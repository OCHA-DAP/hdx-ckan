'''
Created on Jul 25, 2014

@author: alexandru-m-g
'''
import pytest
import logging as logging

import ckan.model as model
import ckan.plugins.toolkit as tk
# import ckan.tests.legacy as tests
import ckan.tests.factories as factories

import ckanext.hdx_theme.tests.hdx_test_base as hdx_test_base

from ckanext.hdx_org_group.helpers.static_lists import ORGANIZATION_TYPE_LIST

log = logging.getLogger(__name__)
_get_action = tk.get_action


class TestDatasetAuth(hdx_test_base.HdxBaseTest):
    @classmethod
    def _load_plugins(cls):
        hdx_test_base.load_plugin('hdx_package hdx_theme')

    def test_create_dataset_with_org(self):
        testsysadmin = model.User.by_name('testsysadmin')
        user = model.User.by_name('tester')

        group_result = factories.Group(name='test_group_e', title='Test Group E')
        org_result = factories.Organization(name='test_org_e', title='Test Org E',
                                            hdx_org_type=ORGANIZATION_TYPE_LIST[0][1],
                                            org_url='https://hdx.hdxtest.org/')

        # result = \
        #     tests.call_action_api(self.app, 'package_create', name='test-dataset',
        #                           private=False, package_creator='test-creator',
        #                           dataset_source='Test Source', license_id='cc-by-igo',
        #                           title='Test Dataset', notes='some_description',
        #                           groups=[{'id':group_result['id']}], owner_org=org_result['id'],
        #                           apikey=user.apikey, status=403)

        try:
            result = _get_action('package_create')(
                {'user': user.name, 'model': model, 'session': model.Session},
                {
                    'name':'test-dataset', 'private': False, 'package_creator': 'test-creator',
                    'dataset_source': 'Test Source', 'license_id': 'cc-by-igo',
                    'title': 'Test Dataset', 'notes': 'some_description',
                    'groups': [{'id':group_result['id']}], 'owner_org': org_result['id']
                }
            )
            assert False, "tester is not part of Test Org E so he can't create a dataset for it"
        except tk.NotAuthorized as e:
            assert True, "tester is not part of Test Org E so he can't create a dataset for it"

        _get_action('organization_member_create')(
            {'user': testsysadmin.name, 'model': model, 'session': model.Session},
            {'id': org_result['id'], 'username': 'tester', 'role': 'editor'}
        )


        # result = \
        #     tests.call_action_api(self.app, 'package_create', name='test-dataset',
        #                           private=False, package_creator='test-creator',
        #                           dataset_source='Test Source', license_id='cc-by-igo',
        #                           title='Test Dataset', notes='some_description',
        #                           groups=[{'id':group_result['id']}], owner_org=org_result['id'],
        #                           apikey=user.apikey, status=200)

        try:
            result = _get_action('package_create')(
                {'user': user.name, 'model': model, 'session': model.Session},
                {
                    'name':'test-dataset', 'private': False, 'package_creator': 'test-creator',
                    'dataset_source': 'Test Source', 'license_id': 'cc-by-igo',
                    'title': 'Test Dataset', 'notes': 'some_description',
                    'groups': [{'id':group_result['id']}], 'owner_org': org_result['id']
                }
            )
            assert True, 'tester is now editor of Test Org E so he can create a dataset for it'
        except tk.NotAuthorized as e:
            assert False, 'tester is now editor of Test Org E so he can create a dataset for it'

