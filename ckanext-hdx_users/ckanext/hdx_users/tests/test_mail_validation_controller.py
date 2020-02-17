'''
Created on Febr 17, 2020

@author: Dan


'''
import logging as logging
import ckan.model as model
import ckan.plugins.toolkit as tk
import ckan.logic as logic
import unicodedata
import ckan.lib.helpers as h
import json

import ckanext.hdx_theme.tests.hdx_test_base as hdx_test_base
import ckanext.hdx_theme.tests.hdx_test_with_inds_and_orgs as hdx_test_with_inds_and_orgs
import ckanext.hdx_users.helpers.permissions as ph

log = logging.getLogger(__name__)
NotFound = logic.NotFound


class TestHDXControllerPage(hdx_test_with_inds_and_orgs.HDXWithIndsAndOrgsTest):

    # @classmethod
    # def _load_plugins(cls):
    #     try:
    #         hdx_test_base.load_plugin('hdx_users hdx_user_extra hdx_package hdx_org_group hdx_theme')
    #     except Exception as e:
    #         log.warn('Module already loaded')
    #         log.info(str(e))

    @classmethod
    def _get_action(cls, action_name):
        return tk.get_action(action_name)

    @classmethod
    def _create_test_data(cls, create_datasets=True, create_members=False):
        super(TestHDXControllerPage, cls)._create_test_data(create_datasets=True, create_members=True)

    def _get_url(self, url, apikey=None):
        if apikey:
            page = self.app.get(url, headers={
                'Authorization': unicodedata.normalize('NFKD', apikey).encode('ascii', 'ignore')})
        else:
            page = self.app.get(url)
        return page

    def test_first_login(self):
        user = model.User.by_name('tester')
        context = {'model': model, 'session': model.Session, 'user': 'tester', 'auth_user_obj': user}
        res = self._get_action('hdx_first_login')(context, {})
        assert res

        user = model.User.by_name('testsysadmin')
        context_sysadmin = {'model': model, 'session': model.Session, 'user': 'testsysadmin', 'auth_user_obj': user}
        res = self._get_action('hdx_first_login')(context_sysadmin, {})
        assert res

        context_nouser = {'model': model, 'session': model.Session}
        try:
            self._get_action('hdx_first_login')(context_nouser, {})
            assert False
        except Exception, ex:
            assert True
            assert 'requires an authenticated user' in ex.message
        assert True

        context_usernotfound = {'model': model, 'session': model.Session, 'user': 'usernotfound', 'auth_user_obj': None}
        try:
            self._get_action('hdx_first_login')(context_usernotfound, {})
            assert False
        except Exception, ex:
            assert True
            assert 'requires an authenticated user' in ex.message
        assert True

    # def test_new_login(self):
        url = h.url_for(controller='ckanext.hdx_users.controllers.mail_validation_controller:ValidationController',
                        action='new_login')
        try:
            res = self._get_url(url, None)
        except Exception, ex:
            assert False
        assert '200' in res.status
        assert 'Forgot your password?' in res.body

        user = model.User.by_name('testsysadmin')
        user.email = 'test@test.com'
        url = h.url_for(controller='ckanext.hdx_users.controllers.mail_validation_controller:ValidationController',
                        action='new_login')
        try:
            res = self._get_url(url, user.apikey)
        except Exception, ex:
            assert False
        assert '200' in res.status
        assert 'Forgot your password?' not in res.body

    # def test_login(self):
        test_url = "/login_generic"
        params = {
            'login': 'testsysadmin',
            'password': 'testsysadmin'
        }
        result = self.app.post(test_url, params=params)
        assert "/user/logged_in?__logins" in result.location
        res = self.app.post(result.location)
        assert True
        assert '302' in res.status
        assert res.c
        assert res.c.action == 'logged_in'
        assert res.c.userobj.name == 'testsysadmin'
