'''
Created on Aug 28, 2014

@author: alexandru-m-g
'''
import pytest
import unicodedata
import logging as logging
import six

import ckan.model as model
import ckan.lib.helpers as h
import ckanext.hdx_theme.helpers.helpers as hdx_h

import ckanext.hdx_theme.tests.hdx_test_base as hdx_test_base

log = logging.getLogger(__name__)

pages = [
    # {'controller': 'ckanext.hdx_users.controllers.registration_controller:RequestController',
    #  'action': 'register', 'usertype': None},
    {'url_name': 'user.login', 'usertype': None},
    {'url_name': 'hdx_contribute_check.contribute', 'usertype': None},
    # {'controller': 'ckanext.hdx_users.controllers.mail_validation_controller:ValidationController',
    #  'action': 'contribute', 'usertype': None},
    {'url_name': 'hdx_dataset.search', 'usertype': 'all'},
    {'url_name': 'hdx_group.index', 'usertype': 'all'},
    {'url_name': 'hdx_org.index', 'usertype': 'all'},
    {'url_name': 'dashboard.organizations', 'usertype': 'all'},
    {'url_name': 'dashboard.index', 'usertype': 'all'},
    {'url_name': 'hdx_user_dashboard.datasets', 'usertype': 'all'},
    {'url_name': 'dashboard.groups', 'usertype': 'all'},
    {'url_name': 'hdx_user_dashboard.datasets', 'usertype': 'all', 'url_params': {'id': 'tester'}},
    {'url_name': 'hdx_splash.about_hrinfo', 'usertype': 'all'},
    {'url_name': 'hdx_splash.index', 'usertype': 'all'},
]

# @pytest.mark.skipif(six.PY3, reason=u"Needed plugins are not on PY3 yet")
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
        # controller = page.get('controller')
        # action = page.get('action')
        url_name = page.get('url_name')
        url_params = page.get('url_params')
        if not page['usertype']:
            self._try_page_load(test_client, url_name, None, url_params)
        else:
            if page['usertype'] == 'user' or page['usertype'] == 'all':
                self._try_page_load(test_client, url_name, 'tester', url_params)
            if page['usertype'] == 'sysadmin' or page['usertype'] == 'all':
                self._try_page_load(test_client, url_name, 'testsysadmin', url_params)

    def _try_page_load(self, test_client, url_name, username, url_params=None):
        result = None
        args = []
        kw = {}
        url_for = h.url_for if url_name and '.' in url_name else hdx_h.url_for
        args.append(url_name)

        if url_params:
            kw = url_params
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
