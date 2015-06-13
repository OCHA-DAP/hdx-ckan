# -*- coding: utf-8 -*-
'''
Created on Oct 1, 2014

@author: alexandru-m-g
'''

import ckan.tests as tests
import ckan.plugins.toolkit as tk
import ckan.model as model

import ckanext.hdx_theme.tests.hdx_test_base as hdx_test_base
import ckanext.hdx_theme.helpers.helpers as hdx_helpers


class TestUserNames(hdx_test_base.HdxBaseTest):

    def test_hdx_linked_user(self):
        admin = model.User.by_name('testsysadmin')
        users = self._users_create(admin.apikey)
        for u in users:
            response = hdx_helpers.hdx_linked_user(u['name'])
            assert u['fullname'] in response,  \
                u['fullname'] + ' should be in the response'

    def _users_create(self, apikey):
        u1 = tests.call_action_api(self.app, 'user_create', name='johnfoo', fullname='Simple user',
                                   email='example@example.com', password='abcd',
                                   apikey=apikey, status=200)
        u2 = tests.call_action_api(self.app, 'user_create', name='adambar', fullname='Test user â',
                                   email='example1@example.com', password='abcd',
                                   apikey=apikey, status=200)
        u3 = tests.call_action_api(self.app, 'user_create', name='frenchuser', fullname='Test ùûüÿ€àâæçéèêëïîôœ',
                                   email='example2@example.com', password='abcd',
                                   apikey=apikey, status=200)

        u4 = tests.call_action_api(self.app, 'user_create', name='romanianuser', fullname='Test user ăâîşșţț„”«»“”',
                                   email='example3@example.com', password='abcd',
                                   apikey=apikey, status=200)

        return [u1, u2, u3, u4]
