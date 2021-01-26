'''
Created on Aug 28, 2014

@author: alexandru-m-g
'''
import pytest
import unicodedata
import logging as logging

import ckan.model as model
import ckan.lib.helpers as h
import ckanext.hdx_theme.helpers.helpers as hdx_h

import ckanext.hdx_theme.tests.hdx_test_base as hdx_test_base

log = logging.getLogger(__name__)

pages = [
    {'controller': 'ckanext.hdx_users.controllers.registration_controller:RequestController',
     'action': 'register', 'usertype': None},
    {'controller': 'user', 'action': 'login', 'usertype': None},
    {'controller': 'ckanext.hdx_users.controllers.mail_validation_controller:ValidationController',
     'action': 'contribute', 'usertype': None},
    {'controller': 'ckanext.hdx_search.controllers.search_controller:HDXSearchController', 'action': 'search', 'usertype': 'all'},
    {'url_name': 'hdx_group.index', 'usertype': 'all'},
    {'url_name': 'hdx_org.index', 'usertype': 'all'},
    {'controller': 'ckanext.hdx_theme.controllers.faq:FaqController', 'action': 'show', 'usertype': 'all'},
    {'controller': 'ckanext.hdx_theme.controllers.faq:FaqController', 'action': 'about', 'usertype': 'all'},
    {'controller': 'ckanext.hdx_theme.controllers.documentation_controller:DocumentationController', 'action': 'show', 'usertype': 'all'},
    {'url_name': 'dashboard.organizations', 'usertype': 'all'},
    {'controller': 'ckanext.hdx_users.controllers.dashboard_controller:DashboardController',
     'action': 'dashboard', 'usertype': 'all'},
    {'controller': 'ckanext.hdx_users.controllers.dashboard_controller:DashboardController',
     'action': 'dashboard_datasets', 'usertype': 'all'},
    {'url_name': 'dashboard.groups', 'usertype': 'all'},
    {'controller': 'ckanext.hdx_package.controllers.dataset_controller:DatasetController',
     'action': 'preselect', 'usertype': 'all'},
    {'controller': 'ckanext.hdx_users.controllers.dashboard_controller:DashboardController', 'action': 'read', 'has_id': True, 'usertype': 'all'},
    {'controller': 'ckanext.hdx_theme.splash_page:SplashPageController', 'action': 'about_hrinfo', 'usertype': 'all'},
    {'controller': 'ckanext.hdx_theme.splash_page:SplashPageController', 'action': 'index', 'usertype': 'all'}
]


class TestPageLoad(hdx_test_base.HdxBaseTest):
    @classmethod
    def _load_plugins(cls):
        hdx_test_base.load_plugin(
            'hdx_search hdx_org_group hdx_package hdx_users hdx_user_extra hdx_pages hdx_theme')

    @classmethod
    def setup_class(cls):

        import ckanext.hdx_users.model as umodel
        import ckanext.hdx_user_extra.model as ue_model
        import ckanext.hdx_pages.model as p_model

        super(TestPageLoad, cls).setup_class()
        umodel.setup()
        ue_model.create_table()
        p_model.create_table()

    @pytest.mark.parametrize("page", pages)
    def test_page_load(self, page):
        # global pages
        test_client = self.get_backwards_compatible_test_client()
        # for page in pages:
        controller = page.get('controller')
        action = page.get('action')
        url_name = page.get('url_name')
        id = page.get('id')
        if not page['usertype']:
            self._try_page_load(test_client, url_name, controller, action, None)
        else:
            id = None
            has_id = page.get('has_id', False)

            if page['usertype'] == 'user' or page['usertype'] == 'all':
                if has_id:
                    id = 'tester'
                self._try_page_load(test_client, url_name, controller, action, 'tester', id)
            if page['usertype'] == 'sysadmin' or page['usertype'] == 'all':
                if has_id:
                    id = 'testsysadmin'
                self._try_page_load(test_client,
                    url_name, controller, action, 'testsysadmin', id)

    def _try_page_load(self, test_client, url_name, controller, action, username, id=None):
        result = None
        args = []
        kw = {}
        url_for = h.url_for if url_name and '.' in url_name else hdx_h.url_for
        if url_name:
            args.append(url_name)
        else:
            kw['controller'] = controller
            kw['action'] = action
        if id:
            kw['id'] = id
        url = url_for(*args, **kw)
        log.info('Testing url: ' + url)
        if username:
            user = model.User.by_name(username)
            result = test_client.get(url, headers={'Authorization': unicodedata.normalize(
                'NFKD', user.apikey).encode('ascii', 'ignore')})
        else:
            result = test_client.get(url)
        assert ('200' in result.status or '302' in result.status), 'HTTP OK'
        assert 'server error' not in str(result.body).lower()
