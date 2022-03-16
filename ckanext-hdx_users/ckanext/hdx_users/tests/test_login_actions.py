'''
Created on Febr 17, 2020

@author: Dan


'''
import logging as logging
import unicodedata

import pytest
import six

import ckan.model as model
import ckan.plugins.toolkit as tk
import ckanext.hdx_theme.tests.hdx_test_base as hdx_test_base

log = logging.getLogger(__name__)
NotFound = tk.ObjectNotFound
config = tk.config
h = tk.h

@pytest.mark.skipif(six.PY3, reason=u'Tests not ready for Python 3')
class TestHDXControllerPage(hdx_test_base.HdxBaseTest):

    @classmethod
    def _get_action(cls, action_name):
        return tk.get_action(action_name)

    def _get_url(self, url, apikey=None):
        if apikey:
            page = self.app.get(url, headers={
                'Authorization': unicodedata.normalize('NFKD', apikey).encode('ascii', 'ignore')})
        else:
            page = self.app.get(url)
        return page

    def test_login_actions(self):
        user = model.User.by_name('tester')
        context = {'model': model, 'session': model.Session, 'user': 'tester', 'auth_user_obj': user}
        login_redirect_result = self._get_action('hdx_first_login')(context, {})
        assert login_redirect_result

        user = model.User.by_name('testsysadmin')
        context_sysadmin = {'model': model, 'session': model.Session, 'user': 'testsysadmin', 'auth_user_obj': user}
        login_redirect_result = self._get_action('hdx_first_login')(context_sysadmin, {})
        assert login_redirect_result

        context_nouser = {'model': model, 'session': model.Session}
        try:
            self._get_action('hdx_first_login')(context_nouser, {})
            assert False
        except Exception as ex:
            assert True
            assert 'requires an authenticated user' in ex.message
        assert True

        context_usernotfound = {'model': model, 'session': model.Session, 'user': 'usernotfound', 'auth_user_obj': None}
        try:
            self._get_action('hdx_first_login')(context_usernotfound, {})
            assert False
        except Exception as ex:
            assert True
            assert 'requires an authenticated user' in ex.message
        assert True

        # test_new_login
        url = h.url_for('hdx_login_link.new_login')
        try:
            login_redirect_result = self._get_url(url, None)
        except Exception as ex:
            assert False
        assert '200' in login_redirect_result.status
        assert 'Forgot your password?' in login_redirect_result.body

        user = model.User.by_name('testsysadmin')
        user.email = 'test@test.com'
        url = h.url_for('hdx_login_link.new_login')
        try:
            login_redirect_result = self._get_url(url, user.apikey)
        except Exception as ex:
            assert False
        assert 200 == login_redirect_result.status_code
        assert 'Forgot your password?' not in login_redirect_result.data

        # test_login
        test_url = "/login_generic"
        params = {
            'login': 'testsysadmin',
            'password': 'testsysadmin'
        }
        test_client = self.get_backwards_compatible_test_client()
        login_result = test_client.post(test_url, data=params)
        assert "/user/logged_in?__logins" in login_result.location
        redirect_location1 = login_result.location.replace(config.get('ckan.site_url'), '')
        login_redirect_result = test_client.post(redirect_location1)
        assert True
        assert 302 == login_redirect_result.status_code
        redirect_location1 = login_redirect_result.location.replace(config.get('ckan.site_url'), '')
        test_client.get(redirect_location1)

        # test logout
        logout_url = '/user/_logout'
        login_redirect_result = test_client.get(logout_url)
        assert 302 == login_redirect_result.status_code
        assert '/user/logout?came_from=/user/logged_out_redirect' in login_redirect_result.data
        try:
            res1 = test_client.get('/user/logout')
            message = '302 Found\n\nThe resource was found at {}/user/logged_out?came_from=%2F; ' \
                      'you should be redirected automatically.'.format(config.get('ckan.site_url'))
            assert message in res1.data
            res2 = test_client.get('/user/logged_out')
            assert False
        except Exception as ex:
            assert 302 == res2.status_code
        assert True
