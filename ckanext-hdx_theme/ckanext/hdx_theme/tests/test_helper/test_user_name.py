# -*- coding: utf-8 -*-
'''
Created on Oct 1, 2014

@author: alexandru-m-g
'''

import ckan.model as model
import ckan.tests.factories as factories


import ckanext.hdx_theme.tests.hdx_test_base as hdx_test_base
import ckanext.hdx_theme.helpers.helpers as hdx_helpers


class TestUserNames(hdx_test_base.HdxBaseTest):

    def test_hdx_linked_user(self):
        admin = model.User.by_name('testsysadmin')
        users = self._users_create()
        for u in users:
            response = hdx_helpers.hdx_linked_user(u['name'])
            assert u['fullname'] in response,  \
                u['fullname'] + ' should be in the response'

    def test_hdx_linked_username(self):
        admin = model.User.by_name('testsysadmin')
        users = self._new_users_create()
        for u in users:
            response_guest = hdx_helpers.hdx_linked_username(u['name'], None)
            response_user = hdx_helpers.hdx_linked_username(u['name'], admin)
            assert not u['fullname'] in response_guest, u['fullname'] + ' shouldn\'t be in the response'
            assert '#loginPopup' in response_guest, '#loginPopup should be in the response'
            assert u['fullname'] in response_user, u['fullname'] + ' should be in the response'

    def _users_create(self):
        u1 = factories.User(name='johnfoo', fullname='Simple user', email='example@example.com')
        u2 = factories.User(name='adambar', fullname='Test user â', email='example1@example.com')

        u3 = factories.User(name='frenchuser', fullname='Test ùûüÿ€àâæçéèêëïîôœ', email='example2@example.com')
        u4 = factories.User(name='romanianuser', fullname='Test user ăâîşșţț„”«»“”', email='example3@example.com')

        return [u1, u2, u3, u4]

    def _new_users_create(self):
        u1 = factories.User(name='johndoe', fullname='John Doe', email='johndoe@example.com')
        u2 = factories.User(name='janedoe', fullname='Jane Doe', email='janedoe@example.com')

        return [u1, u2]
