'''
Created on Dec 8, 2014

@author: alexandru-m-g
'''

import unicodedata
import json
import logging as logging
from nose.tools import (assert_equal,
                        assert_true,
                        assert_false,
                        assert_not_equal)
import ckan.model as model
import ckanext.hdx_users.model as umodel
import ckan.tests as tests
import ckan.new_tests.helpers as test_helpers
import ckan.lib.helpers as h
import ckanext.hdx_user_extra.model as ue_model

import ckanext.hdx_theme.tests.hdx_test_base as hdx_test_base


class TestEmailAccess(hdx_test_base.HdxBaseTest):
    @classmethod
    def _load_plugins(cls):
        hdx_test_base.load_plugin(
            'hdx_org_group hdx_package hdx_mail_validate hdx_users hdx_user_extra hdx_theme')

    @classmethod
    def setup_class(cls):
        super(TestEmailAccess, cls).setup_class()
        umodel.setup()
        ue_model.create_table()

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
        res = self._create_user()
        user = model.User.get('valid@example.com')
        assert user
        token = umodel.ValidationToken.get(user.id)
        assert token

    def test_no_duplicate_tokens(self):
        res = self._create_user()
        try:
            res2 = self._create_user()
            assert False
        except:
            assert True


    def test_delete_user(self):
        res = self._create_user()

        user = model.User.get('valid@example.com')
        admin = model.User.by_name('testsysadmin')
        offset2 = h.url_for(controller='user', action='delete', id=user.id)
        res2 = self.app.get(offset2, status=[200, 302], headers={'Authorization': unicodedata.normalize(
            'NFKD', admin.apikey).encode('ascii', 'ignore')})

        profile_url = h.url_for(controller='user', action='read', id='valid@example.com')

        profile_result = self.app.get(profile_url, headers={'Authorization': unicodedata.normalize(
            'NFKD', admin.apikey).encode('ascii', 'ignore')})
        non_admin = model.User.by_name('tester')
        profile_result2 = self.app.get(profile_url, status=[404], headers={'Authorization': unicodedata.normalize(
            'NFKD', non_admin.apikey).encode('ascii', 'ignore')})

        assert '404' in profile_result2.status

        assert '<span class="label label-important">Deleted</span>' in str(profile_result.response)

    def _create_user(self, email='valid@example.com'):
        url = h.url_for(controller='ckanext.hdx_users.controllers.mail_validation_controller:ValidationController',
                        action='register_email')
        params = {'email': email}
        res = self.app.post(url, params)
        return res


class TestUserEmailRegistration(hdx_test_base.HdxBaseTest):

    @classmethod
    def _load_plugins(cls):
        hdx_test_base.load_plugin(
            'hdx_org_group hdx_package hdx_mail_validate hdx_users hdx_user_extra hdx_theme')

    def test_create_user(self):
        '''Creating a new user is successful.'''
        user_list = test_helpers.call_action('user_list')
        before_len = len(user_list)

        url = h.url_for(controller='ckanext.hdx_users.controllers.mail_validation_controller:ValidationController',
                        action='register_email')
        params = {'email': 'valid@example.com'}
        res = self.app.post(url, params)
        assert_true(json.loads(res.body)['success'])

        user = model.User.get('valid@example.com')

        assert_true(user is not None)
        assert_true(user.password is None)

        user_list = test_helpers.call_action('user_list')
        after_len = len(user_list)
        assert_equal(after_len, before_len+1)

    def test_create_user_duplicate_email(self):
        '''Creating a new user with identical email is unsuccessful.'''
        url = h.url_for(controller='ckanext.hdx_users.controllers.mail_validation_controller:ValidationController',
                        action='register_email')
        params = {'email': 'valid@example.com'}
        # create 1
        self.app.post(url, params)
        # create 2
        res = json.loads(self.app.post(url, params).body)
        assert_false(res['success'])
        assert_equal(res['error']['message'],
                     u'That login email is not available.')

    def test_create_user_duplicate_email_case_different(self):
        '''Creating a new user with same email (differently cased) is
        unsuccessful.'''
        url = h.url_for(controller='ckanext.hdx_users.controllers.mail_validation_controller:ValidationController',
                        action='register_email')
        params_one = {'email': 'valid@example.com'}
        params_two = {'email': 'Valid@example.com'}
        # create 1
        self.app.post(url, params_one)
        # create 2
        res = json.loads(self.app.post(url, params_two).body)
        assert_false(res['success'])
        assert_equal(res['error']['message'],
                     u'That login email is not available.')

    def test_create_user_email_saved_as_lowercase(self):
        '''A newly created user will have their email transformed to lowercase
        before saving.'''
        url = h.url_for(controller='ckanext.hdx_users.controllers.mail_validation_controller:ValidationController',
                        action='register_email')
        params = {'email': 'VALID@example.com'}
        self.app.post(url, params)
        user = model.User.get('valid@example.com')
        # retrieved user has lowercase email
        assert_equal(user.email, 'valid@example.com')
        assert_not_equal(user.email, 'VALID@example.com')

    def test_create_user_email_format(self):
        '''Email must be valid email format.'''
        url = h.url_for(controller='ckanext.hdx_users.controllers.mail_validation_controller:ValidationController',
                        action='register_email')
        params = {'email': 'invalidexample.com'}

        res = json.loads(self.app.post(url, params).body)
        assert_equal(res['error']['message'],
                     u'Email address is not valid')

    #TODO create user according to the last onboarding. Note CAPTCHA!
    # def test_login_not_valid(self):
    #     offset = h.url_for(controller='ckanext.hdx_users.controllers.mail_validation_controller:ValidationController', action='register')
    #     res = self.app.get(offset, status=[200,302])
    #     fv = res.forms[1]
    #     fv['name'] = "testingvalid"
    #     fv['fullname'] = "Valid Test"
    #     fv['email'] = "valid@example.com"
    #     fv['password1'] = "password"
    #     fv['password2'] = "password"
    #     res = fv.submit('save')
    #
    #     user = model.User.by_name('testingvalid')
    #
    #     offset = h.url_for(controller='user', action='login')
    #     res = self.app.get(offset)
    #     fv = res.forms[1]
    #     fv['login'] = user.name
    #     fv['password'] = 'password'
    #     res = fv.submit()
    #
    #     # first get redirected to logged_in
    #     assert '302' in res.status
    #     # then get redirected to login
    #     res = res.follow()
    #     assert res.headers['Location'].startswith('http://localhost/user/logged_in') or \
    #            res.header('Location').startswith('/user/logged_in')
    #     res = res.follow()
    #     assert res.headers['Location'].startswith('http://localhost/user/logout') or \
    #            res.header('Location').startswith('/user/logout')

        # def test_validate_account(self):
        #     offset = h.url_for(controller='ckanext.hdx_users.controllers.mail_validation_controller:ValidationController', action='register')
        #     res = self.app.get(offset, status=[200,302])
        #     fv = res.forms[1]
        #     fv['name'] = "testingvalid"
        #     fv['fullname'] = "Valid Test"
        #     fv['email'] = "valid@example.com"
        #     fv['password1'] = "password"
        #     fv['password2'] = "password"
        #     res = fv.submit('save')

        #     user = model.User.by_name('testingvalid')
        #     assert user
        #     token = umodel.ValidationToken.get(user.id)
        #     assert token

        #     offset = h.url_for(controller='ckanext.hdx_users.controllers.mail_validation_controller:ValidationController', action='validate', token=token.token)
        #     res = self.app.get(offset, status=[200,302])

        #     token = umodel.ValidationToken.get(user.id)
        #     assert token.valid is True
