'''
Created on Dec 8, 2014

@author: alexandru-m-g
'''

import unicodedata
import logging as logging
from nose.tools import assert_equal
import ckan.model as model
import ckanext.hdx_users.model as umodel
import ckan.tests as tests
import ckan.lib.helpers as h
from ckan.tests import CreateTestData

import ckanext.hdx_theme.tests.hdx_test_base as hdx_test_base


class TestEmailAccess(hdx_test_base.HdxBaseTest):

    @classmethod
    def _load_plugins(cls):
        hdx_test_base.load_plugin(
            'hdx_org_group hdx_package hdx_mail_validate hdx_users hdx_theme')

    @classmethod
    def setup_class(cls):
        super(TestEmailAccess, cls).setup_class()
        umodel.setup()

        cls._get_action('user_create')({
            'model': model, 'session': model.Session, 'user': 'testsysadmin'},
            {'name': 'johnfoo', 'fullname': 'John Foo',
             'email': 'example@example.com', 'password': 'abcd'})


    @classmethod
    def _get_action(cls, action_name):
        return tests.get_action(action_name)

    def test_email_access_by_page(self):
        admin = model.User.by_name('testsysadmin')

        url = h.url_for(controller='user', action='index')
        profile_url = h.url_for(controller='user', action='read', id='johnfoo')

        result = self.app.get(url, headers={'Authorization': unicodedata.normalize(
            'NFKD', admin.apikey).encode('ascii', 'ignore')})

        profile_result = self.app.get(url, headers={'Authorization': unicodedata.normalize(
            'NFKD', admin.apikey).encode('ascii', 'ignore')})

        assert 'example@example.com' in str(result.response)
        assert 'example@example.com' in str(profile_result.response)

        user = model.User.by_name('tester')
        result = self.app.get(url, headers={'Authorization': unicodedata.normalize(
            'NFKD', user.apikey).encode('ascii', 'ignore')})
        profile_result = self.app.get(url, headers={'Authorization': unicodedata.normalize(
            'NFKD', user.apikey).encode('ascii', 'ignore')})

        assert 'example@example.com' not in str(
            result.response), 'emails should not be visible for normal users'
        assert 'example@example.com' not in str(
            profile_result.response), 'emails should not be visible for normal users'

        result = self.app.get(url)
        profile_result = self.app.get(profile_url)

        assert 'example@example.com' not in str(
            result.response), 'emails should not be visible for guests'
        assert 'example@example.com' not in str(
            profile_result.response), 'emails should not be visible for guests'

    def test_email_access_by_api(self):

        user_list = self._get_action('user_list')({
            'model': model, 'session': model.Session, 'user': 'testsysadmin'}, {})
        assert self._user_list_has_email(user_list, 'testsysadmin')
        user = self._get_action('user_show')({
            'model': model, 'session': model.Session, 'user': 'testsysadmin'}, {'id': 'johnfoo'})
        assert 'email' in user

        user_list = self._get_action('user_list')({
            'model': model, 'session': model.Session, 'user': 'tester'}, {})
        assert not self._user_list_has_email(
            user_list, 'tester'), 'emails should not be visible for normal users'
        user = self._get_action('user_show')({
            'model': model, 'session': model.Session, 'user': 'tester'},
            {'id': 'johnfoo'})
        assert not 'email' in user, 'emails should not be visible for normal users'

        user_list = self._get_action('user_list')({
            'model': model, 'session': model.Session}, {})
        assert not self._user_list_has_email(
            user_list),  'emails should not be visible for guests'
        user = self._get_action('user_show')({
            'model': model, 'session': model.Session}, {'id': 'johnfoo'})
        assert not 'email' in user,  'emails should not be visible for guests'

    def _user_list_has_email(self, users, current_username=''):
        if users:
            for user in users:
                if 'email' in user and current_username != user['name']:
                    return True

        return False

    def test_create_validation_token(self):
        offset = h.url_for(controller='ckanext.hdx_users.controllers.mail_validation_controller:ValidationController', action='register')
        res = self.app.get(offset, status=[200,302])
        fv = res.forms[1]
        fv['name'] = "testingvalid"
        fv['fullname'] = "Valid Test"
        fv['email'] = "valid@example.com"
        fv['password1'] = "password"
        fv['password2'] = "password"
        res = fv.submit('save')

        user = model.User.by_name('testingvalid')
        assert user
        token = umodel.ValidationToken.get(user.id)
        assert token

    def test_login_not_valid(self):
        offset = h.url_for(controller='ckanext.hdx_users.controllers.mail_validation_controller:ValidationController', action='register')
        res = self.app.get(offset, status=[200,302])
        fv = res.forms[1]
        fv['name'] = "testingvalid"
        fv['fullname'] = "Valid Test"
        fv['email'] = "valid@example.com"
        fv['password1'] = "password"
        fv['password2'] = "password"
        res = fv.submit('save')

        user = model.User.by_name('testingvalid')

        offset = h.url_for(controller='user', action='login')
        res = self.app.get(offset)
        fv = res.forms[1]
        fv['login'] = user.name
        fv['password'] = 'password'
        res = fv.submit()

        # first get redirected to logged_in
        assert '302' in res.status
        # then get redirected to login
        res = res.follow()
        assert res.headers['Location'].startswith('http://localhost/user/logged_in') or \
               res.header('Location').startswith('/user/logged_in')
        res = res.follow()
        assert res.headers['Location'].startswith('http://localhost/user/logout') or \
               res.header('Location').startswith('/user/logout')
        
    def test_validate_account(self):
        offset = h.url_for(controller='ckanext.hdx_users.controllers.mail_validation_controller:ValidationController', action='register')
        res = self.app.get(offset, status=[200,302])
        fv = res.forms[1]
        fv['name'] = "testingvalid"
        fv['fullname'] = "Valid Test"
        fv['email'] = "valid@example.com"
        fv['password1'] = "password"
        fv['password2'] = "password"
        res = fv.submit('save')

        user = model.User.by_name('testingvalid')
        assert user
        token = umodel.ValidationToken.get(user.id)
        assert token

        offset = h.url_for(controller='ckanext.hdx_users.controllers.mail_validation_controller:ValidationController', action='validate', token=token.token)
        res = self.app.get(offset, status=[200,302])

        token = umodel.ValidationToken.get(user.id)
        assert token.valid is True
