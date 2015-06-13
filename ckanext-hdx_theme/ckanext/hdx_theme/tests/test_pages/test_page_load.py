'''
Created on Aug 28, 2014

@author: alexandru-m-g
'''

import unicodedata
import logging as logging

import ckan.model as model
import ckan.lib.helpers as h

import ckanext.hdx_theme.tests.hdx_test_base as hdx_test_base

pages = [
    {'controller': 'ckanext.hdx_users.controllers.registration_controller:RequestController',
        'action': 'register', 'usertype': None},
    {'controller': 'user',
        'action': 'login', 'usertype': None},
    {'controller': 'ckanext.hdx_users.controllers.login_controller:LoginController',
        'action': 'contribute', 'usertype': None},
    {'controller': 'package',
        'action': 'search', 'usertype': 'all'},
    {'controller': 'group',
        'action': 'index', 'usertype': 'all'},
    {'controller': 'organization',
        'action': 'index', 'usertype': 'all'},
    {'controller': 'home',
        'action': 'about', 'usertype': 'all'},
    {'controller': 'user',
        'action': 'dashboard_organizations', 'usertype': 'all'},
    {'controller': 'ckanext.hdx_users.controllers.dashboard_controller:DashboardController',
        'action': 'dashboard', 'usertype': 'all'},
    {'controller': 'ckanext.hdx_users.controllers.dashboard_controller:DashboardController',
        'action': 'dashboard_datasets', 'usertype': 'all'},
    {'controller': 'user',
        'action': 'dashboard_groups', 'usertype': 'all'},
    {'controller': 'ckanext.hdx_package.controllers.dataset_controller:DatasetController',
        'action': 'preselect', 'usertype': 'all'},
    {'controller': 'user',
        'action': 'dashboard_groups', 'usertype': 'all'},
    {'controller': 'user', 'action': 'read',
        'has_id': True, 'usertype': 'all'}
]


class TestPageLoad(hdx_test_base.HdxBaseTest):

    @classmethod
    def _load_plugins(cls):
        hdx_test_base.load_plugin(
            'hdx_org_group hdx_package hdx_users hdx_theme')

    def test_page_load(self):
        global pages
        for page in pages:
            controller = page['controller']
            action = page['action']
            id = page.get('id')
            if not page['usertype']:
                self._try_page_load(controller, action, None)
            else:
                id = None
                has_id = page.get('has_id', False)

                if page['usertype'] == 'user' or page['usertype'] == 'all':
                    if has_id:
                        id = 'tester'
                    self._try_page_load(controller, action, 'tester', id)
                if page['usertype'] == 'sysadmin' or page['usertype'] == 'all':
                    if has_id:
                        id = 'testsysadmin'
                    self._try_page_load(
                        controller, action, 'testsysadmin', id)

    def _try_page_load(self, controller, action, username, id=None):
        result = None
        url = h.url_for(
            controller=controller, action=action, id=id)
        if username:
            user = model.User.by_name(username)
            result = self.app.get(url, headers={'Authorization': unicodedata.normalize(
                'NFKD', user.apikey).encode('ascii', 'ignore')})
        else:
            result = self.app.get(url)
        assert '200' in result.response.status, 'HTTP OK'
        assert 'server error' not in str(result.body).lower()
