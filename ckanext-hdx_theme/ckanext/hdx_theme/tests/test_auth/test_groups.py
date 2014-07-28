'''
Created on Jul 24, 2014

@author: alexandru-m-g
'''

import logging as logging
import ckan.model as model
import ckan.tests as tests

import ckanext.hdx_theme.tests.hdx_test_base as hdx_test_base

log = logging.getLogger(__name__)


class TestGroupAuth(hdx_test_base.HdxBaseTest):

    def test_create_country(self):
        user = model.User.by_name('tester')
        tests.call_action_api(self.app, 'group_create', name='test_group_a',
                              title='Test Group A',
                              apikey=user.apikey, status=403)
        assert True

    def test_edit_country(self):
        testsysadmin = model.User.by_name('testsysadmin')
        user = model.User.by_name('tester')
        create_result = tests.call_action_api(self.app, 'group_create',
                                              name='test_group_b', title='Test Group B',
                                              apikey=testsysadmin.apikey, status=200)
        tests.call_action_api(self.app, 'group_update', id=create_result['id'],
                                       title='Test Group B CHANGED',
                                       apikey=user.apikey, status=403)
        assert True, 'user should not be allowed to modify the group'

    def test_delete_country(self):
        testsysadmin = model.User.by_name('testsysadmin')
        user = model.User.by_name('tester')
        create_result = tests.call_action_api(self.app, 'group_create',
                                              name='test_group_c', title='Test Group C',
                                              apikey=testsysadmin.apikey, status=200)
        tests.call_action_api(self.app, 'group_delete', id=create_result['id'],
                                       apikey=user.apikey, status=403)
        assert True, 'user should not be allowed to delete the group'

    def test_create_country_member(self):
        testsysadmin = model.User.by_name('testsysadmin')
        create_result = tests.call_action_api(self.app, 'group_create',
                                              name='test_group_d', title='Test Group D',
                                              apikey=testsysadmin.apikey, status=200)
        tests.call_action_api(self.app, 'group_member_create',
                              id=create_result['id'], username='tester', role='editor',
                              apikey=testsysadmin.apikey, status=403)
        assert True, 'Country members shouldn\'t be allowed'
