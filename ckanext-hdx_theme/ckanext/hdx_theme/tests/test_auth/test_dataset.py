'''
Created on Jul 25, 2014

@author: alexandru-m-g
'''

import logging as logging
import ckan.model as model
import ckan.tests as tests

import ckanext.hdx_theme.tests.hdx_test_base as hdx_test_base

log = logging.getLogger(__name__)


class TestDatasetAuth(hdx_test_base.HdxBaseTest):
    @classmethod
    def _load_plugins(cls):
        hdx_test_base.load_plugin('hdx_package hdx_theme')

    def test_create_dataset_with_org(self):
        testsysadmin = model.User.by_name('testsysadmin')
        user = model.User.by_name('tester')

        group_result = tests.call_action_api(self.app, 'group_create',
                                             name='test_group_e', title='Test Group E',
                                             apikey=testsysadmin.apikey, status=200)
        org_result = \
            tests.call_action_api(self.app, 'organization_create', name='test_org_e',
                                  title='Test Org E',
                                  apikey=testsysadmin.apikey, status=200)

        result = \
            tests.call_action_api(self.app, 'package_create', name='test-dataset',
                                  private=False, package_creator='test-creator',
                                  dataset_source='Test Source', license_id='cc-by-igo',
                                  title='Test Dataset', notes='some_description',
                                  groups=[{'id':group_result['id']}], owner_org=org_result['id'],
                                  apikey=user.apikey, status=403)
        assert True, "tester is not part of Test Org E so he can't create a dataset for it"

        tests.call_action_api(self.app, 'organization_member_create',
                              id=org_result['id'], username='tester', role='editor',
                              apikey=testsysadmin.apikey, status=200)

        result = \
            tests.call_action_api(self.app, 'package_create', name='test-dataset',
                                  private=False, package_creator='test-creator',
                                  dataset_source='Test Source', license_id='cc-by-igo',
                                  title='Test Dataset', notes='some_description',
                                  groups=[{'id':group_result['id']}], owner_org=org_result['id'],
                                  apikey=user.apikey, status=200)
            
        assert True, "tester is now editor of Test Org E so he can create a dataset for it"
