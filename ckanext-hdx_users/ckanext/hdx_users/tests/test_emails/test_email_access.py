'''
Created on Dec 8, 2014

@author: alexandru-m-g
'''

import pytest

import unicodedata
import json
from nose.tools import (assert_equal,
                        assert_true,
                        assert_false,
                        assert_not_equal)

import ckan.model as model
import ckanext.hdx_users.model as umodel
import ckan.tests.helpers as test_helpers
import ckan.lib.helpers as h
import ckan.plugins.toolkit as tk
import ckanext.hdx_theme.tests.hdx_test_base as hdx_test_base
# from ckan.tests.legacy.mock_mail_server import SmtpServerHarness
# from ckan.tests.legacy.pylons_controller import PylonsTestCase
from ckan.tests import factories
import ckanext.hdx_users.controllers.mailer as hdx_mailer
from urlparse import urljoin
import ckanext.hdx_users.helpers.reset_password as reset_password


# webtest_submit = test_helpers.webtest_submit
# submit_and_follow = test_helpers.submit_and_follow

# @pytest.mark.skip(reason='Many functions and objects no longer available in 2.9')
class TestEmailAccess(hdx_test_base.HdxFunctionalBaseTest):
    @classmethod
    def setup_class(cls):
        super(TestEmailAccess, cls).setup_class()

        cls._get_action('user_create')({
            'model': model, 'session': model.Session, 'user': 'testsysadmin'},
            {'name': 'johnfoo', 'fullname': 'John Foo',
             'email': 'example@example.com', 'password': 'abcdefgh'})

    @classmethod
    def _get_action(cls, action_name):
        return tk.get_action(action_name)

    def test_email_access_by_page(self):
        admin = model.User.by_name('testsysadmin')

        url = h.url_for('user.index')[:-1]
        profile_url = h.url_for(controller='user', action='read', id='johnfoo')

        result = self.app.get(url, headers={'Authorization': unicodedata.normalize(
            'NFKD', admin.apikey).encode('ascii', 'ignore')})

        profile_result = self.app.get(url, headers={'Authorization': unicodedata.normalize(
            'NFKD', admin.apikey).encode('ascii', 'ignore')})

        assert 'example@example.com' in str(result.body)
        assert 'example@example.com' in str(profile_result.body)

        user = model.User.by_name('tester')
        result = self.app.get(url, headers={'Authorization': unicodedata.normalize(
            'NFKD', user.apikey).encode('ascii', 'ignore')})
        profile_result = self.app.get(url, headers={'Authorization': unicodedata.normalize(
            'NFKD', user.apikey).encode('ascii', 'ignore')})

        assert 'example@example.com' not in str(
            result.body), 'emails should not be visible for normal users'
        assert 'example@example.com' not in str(
            profile_result.body), 'emails should not be visible for normal users'

        result = self.app.get(url)
        profile_result = self.app.get(profile_url)

        assert 'example@example.com' not in str(
            result.body), 'emails should not be visible for guests'
        assert 'example@example.com' not in str(
            profile_result.body), 'emails should not be visible for guests'

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
            user_list), 'emails should not be visible for guests'
        user = self._get_action('user_show')({
            'model': model, 'session': model.Session}, {'id': 'johnfoo'})
        assert not 'email' in user, 'emails should not be visible for guests'

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
        offset2 = str(h.url_for('user.delete', id=user.id))
        res2 = self.app.post(offset2, status=200, headers={'Authorization': unicodedata.normalize(
            'NFKD', admin.apikey).encode('ascii', 'ignore')})

        profile_url = h.url_for(controller='user', action='read', id='valid@example.com')

        profile_result = self.app.get(profile_url, headers={'Authorization': unicodedata.normalize(
            'NFKD', admin.apikey).encode('ascii', 'ignore')})
        non_admin = model.User.by_name('tester')
        profile_result2 = self.app.get(profile_url, status=404, headers={'Authorization': unicodedata.normalize(
            'NFKD', non_admin.apikey).encode('ascii', 'ignore')})

        assert '404' in profile_result2.status

        assert '<span class="label label-important">Deleted</span>' in profile_result.data

    def _create_user(self, email='valid@example.com'):
        url = h.url_for(controller='ckanext.hdx_users.controllers.mail_validation_controller:ValidationController',
                        action='register_email')
        params = {'email': email, 'nosetest': 'true'}
        res = self.app.post(url, data=params)
        return res


class TestUserEmailRegistration(hdx_test_base.HdxFunctionalBaseTest):
    @classmethod
    def setup_class(cls):
        super(TestUserEmailRegistration, cls).setup_class()
        # umodel.setup()
        # ue_model.create_table()

    def setup(self):
        test_helpers.reset_db()
        test_helpers.search.clear_all()

    def test_create_user(self):
        '''Creating a new user is successful.'''
        user_list = test_helpers.call_action('user_list')
        before_len = len(user_list)

        url = h.url_for(controller='ckanext.hdx_users.controllers.mail_validation_controller:ValidationController',
                        action='register_email')
        params = {'email': 'valid@example.com', 'nosetest': 'true'}
        res = self.app.post(url, data=params)
        assert_true(json.loads(res.body)['success'])

        user = model.User.get('valid@example.com')

        assert_true(user is not None)
        assert_true(user.password is None)

        user_list = test_helpers.call_action('user_list')
        after_len = len(user_list)
        assert_equal(after_len, before_len + 1)

    def test_create_user_duplicate_email(self):
        '''Creating a new user with identical email is unsuccessful.'''
        url = h.url_for(controller='ckanext.hdx_users.controllers.mail_validation_controller:ValidationController',
                        action='register_email')
        params = {'email': 'valid@example.com', 'nosetest': 'true'}
        # create 1
        self.app.post(url, data=params)
        # create 2
        res = json.loads(self.app.post(url, data=params).body)
        assert_false(res['success'])
        assert_equal(res['error']['message'][0],
                     'The email address is already registered on HDX. Please use the sign in screen below.')

    def test_create_user_duplicate_email_case_different(self):
        '''Creating a new user with same email (differently cased) is
        unsuccessful.'''
        url = h.url_for(controller='ckanext.hdx_users.controllers.mail_validation_controller:ValidationController',
                        action='register_email')
        params_one = {'email': 'valid@example.com', 'nosetest': 'true'}
        params_two = {'email': 'VALID@example.com', 'nosetest': 'true'}
        # create 1
        self.app.post(url, data=params_one)
        # create 2
        response = self.app.post(url, data=params_two)
        res = json.loads(response.data)
        assert_false(res['success'])
        assert_equal(res['error']['message'][0],
                     'The email address is already registered on HDX. Please use the sign in screen below.')

    def test_create_user_email_saved_as_lowercase(self):
        '''A newly created user will have their email transformed to lowercase
        before saving.'''
        url = h.url_for(controller='ckanext.hdx_users.controllers.mail_validation_controller:ValidationController',
                        action='register_email')
        params = {'email': 'VALID@example.com', 'nosetest': 'true'}
        self.app.post(url, data=params)
        user = model.User.get('valid@example.com')
        # retrieved user has lowercase email
        assert_equal(user.email, 'valid@example.com')
        assert_not_equal(user.email, 'VALID@example.com')

    def test_create_user_email_format(self):
        '''Email must be valid email format.'''
        url = h.url_for(controller='ckanext.hdx_users.controllers.mail_validation_controller:ValidationController',
                        action='register_email')
        params = {'email': 'invalidexample.com', 'nosetest': 'true'}

        res = json.loads(self.app.post(url, data=params).data)
        assert_equal(res['error']['message'][0], u'Email invalidexample.com is not a valid format')


# Below imports and definitions are needed so that the tests below don't give an error when running pytest.
# The tests will be skipped for now as many functions and objects no longer available in 2.9
import hashlib
import ckanext.hdx_user_extra.model as ue_model

config = tk.config


# class SmtpServerHarness(object):
#     pass
#
#
# class PylonsTestCase(object):
#     pass
#
#
# submit_and_follow = None
# webtest_submit = None


def _get_user_params(user_dict):
    params = {
        'old_password': 'abcdefgh',
        'email': user_dict.get('email'),
        'save': 'True',
        'password1': '',
        'password2': '',
        'name': user_dict.get('name'),
        'firstname': 'Sue',
        'lastname': 'User',
        'id': user_dict.get('id'),
        'about': user_dict.get('about')
    }
    return params

class TestEditUserEmail(hdx_test_base.HdxFunctionalBaseTest):
    @classmethod
    def setup_class(cls):
        super(TestEditUserEmail, cls).setup_class()
        # umodel.setup()
        # ue_model.create_table()

    def setup(self):
        test_helpers.reset_db()
        test_helpers.search.clear_all()

    def test_edit_email(self):
        '''Editing an existing user's email is successful.'''
        sue_user = factories.User(name='sue', email='sue@example.com', password='abcdefgh')

        sue_obj = model.User.get('sue@example.com')
        sue_obj.apikey = 'SUE_API_KEY'
        model.Session.commit()

        env = {'REMOTE_USER': sue_user['name'].encode('ascii')}
        url_for = h.url_for('user.edit')
        response = self.app.get(
            url=url_for,
            extra_environ=env,
        )
        # existing values in the form
        assert '<input id="field-username" type="text" name="name" value="sue"' in response.body
        assert '<input id="field-firstname" type="text" name="firstname" value="Mr. Test User"' in response.body
        assert '<input id="field-lastname" type="text" name="lastname" value=""' in response.body
        assert '<input id="field-email" type="email" name="email" value="sue@example.com"' in response.body
        assert '<textarea id="field-about" name="about" cols="20" rows="5" placeholder="A little information about yourself"' in response.body
        assert '<input id="field-activity-streams-email-notifications" type="checkbox" name="activity_streams_email_notifications" value="True"' in response.body
        assert '<input id="field-password" type="password" name="old_password" value=""' in response.body
        assert '<input id="field-password" type="password" name="password1" value=""' in response.body
        assert '<input id="field-password-confirm" type="password" name="password2" value=""' in response.body

        user_dict = tk.get_action('user_show')({
            'model': model, 'session': model.Session, 'user': 'testsysadmin'},
            {'id': 'sue@example.com'})
        test_client = self.get_backwards_compatible_test_client()
        params = _get_user_params(user_dict)
        params['email'] = 'new@example.com'
        auth = {'Authorization': str(sue_obj.apikey)}
        user_updated = test_client.post(url_for, data=params, extra_environ=auth)

        user = model.Session.query(model.User).get(sue_user['id'])
        assert_equal(user.email, 'new@example.com')

    def test_edit_email_to_existing(self):
        '''Editing to an existing user's email is unsuccessful.'''
        factories.User(name='existing', email='existing@example.com')
        sue_user = factories.User(name='sue', email='sue@example.com', password='abcdefgh')
        sue_obj = model.User.get('sue@example.com')
        sue_obj.apikey = 'SUE_API_KEY'
        model.Session.commit()

        env = {'REMOTE_USER': sue_user['name'].encode('ascii')}
        url_for = h.url_for('user.edit')
        response = self.app.get(
            url=url_for,
            extra_environ=env,
        )
        # existing email in the form
        assert '<input id="field-email" type="email" name="email" value="sue@example.com"' in response.body

        user_dict = tk.get_action('user_show')({
            'model': model, 'session': model.Session, 'user': 'testsysadmin'},
            {'id': 'sue@example.com'})
        test_client = self.get_backwards_compatible_test_client()
        params = _get_user_params(user_dict)
        params['email'] = 'existing@example.com'
        auth = {'Authorization': str(sue_obj.apikey)}
        user_updated = test_client.post(url_for, data=params, extra_environ=auth)

        # error message in response
        assert '<li data-field-label="Email">Email: The email address is already registered on HDX. Please use the sign in screen below.</li>' in user_updated.body

        # sue user email hasn't changed.
        user = model.Session.query(model.User).get(sue_user['id'])
        assert_equal(user.email, 'sue@example.com')

    def test_edit_email_invalid_format(self):
        '''Editing with an invalid email format is unsuccessful.'''
        sue_user = factories.User(name='sue', email='sue@example.com', password='abcdefgh')
        sue_obj = model.User.get('sue@example.com')
        sue_obj.apikey = 'SUE_API_KEY'
        model.Session.commit()

        env = {'REMOTE_USER': sue_user['name'].encode('ascii')}
        url_for = h.url_for('user.edit')
        response = self.app.get(
            url=url_for,
            extra_environ=env,
        )
        # existing email in the form
        assert '<input id="field-email" type="email" name="email" value="sue@example.com"' in response.body

        user_dict = tk.get_action('user_show')({
            'model': model, 'session': model.Session, 'user': 'testsysadmin'},
            {'id': 'sue@example.com'})
        test_client = self.get_backwards_compatible_test_client()
        params = _get_user_params(user_dict)
        params['email'] = 'invalid.com'
        auth = {'Authorization': str(sue_obj.apikey)}
        user_updated = test_client.post(url_for, data=params, extra_environ=auth)

        # error message in response
        assert '<li data-field-label="Email">Email: Email {} is not a valid format</li>'.format(params['email']) in user_updated.body

        # sue user email hasn't changed.
        user = model.Session.query(model.User).get(sue_user['id'])
        assert_equal(user.email, 'sue@example.com')

    def test_edit_email_saved_as_lowercase(self):
        '''Editing with an email in uppercase will be saved as lowercase.'''
        existing_user = factories.User(name='existing', email='existing@example.com', password='abcdefgh')
        sue_user = factories.User(name='sue', email='sue@example.com', password='abcdefgh')

        sue_obj = model.User.get('sue@example.com')
        sue_obj.apikey = 'SUE_API_KEY'
        model.Session.commit()

        env = {'REMOTE_USER': sue_user['name'].encode('ascii')}
        url_for = h.url_for('user.edit')
        response = self.app.get(
            url=url_for,
            extra_environ=env,
        )
        # existing values in the form
        assert '<input id="field-email" type="email" name="email" value="sue@example.com"' in response.body

        user_dict = tk.get_action('user_show')({
            'model': model, 'session': model.Session, 'user': 'testsysadmin'},
            {'id': 'sue@example.com'})
        test_client = self.get_backwards_compatible_test_client()
        params = _get_user_params(user_dict)
        params['email'] = 'existing@example.com'
        auth = {'Authorization': str(sue_obj.apikey)}
        user_updated = test_client.post(url_for, data=params, extra_environ=auth)
        assert '<li data-field-label="Email">Email: The email address is already registered on HDX. Please use the sign in screen below.</li>' in user_updated.body

        user = model.Session.query(model.User).get(sue_user['id'])
        assert_equal(user.email, sue_user.get('email'))

    def test_edit_email_differently_case_existing(self):
        '''Editing with an existing user's email will be unsuccessful, even is
        differently cased.'''
        '''Editing with an email in uppercase will be saved as lowercase.'''
        existing_user = factories.User(name='existing', email='existing@example.com', password='abcdefgh')
        sue_user = factories.User(name='sue', email='sue@example.com', password='abcdefgh')

        sue_obj = model.User.get('sue@example.com')
        sue_obj.apikey = 'SUE_API_KEY'
        model.Session.commit()

        env = {'REMOTE_USER': sue_user['name'].encode('ascii')}
        url_for = h.url_for('user.edit')
        response = self.app.get(
            url=url_for,
            extra_environ=env,
        )
        # existing values in the form
        assert '<input id="field-email" type="email" name="email" value="sue@example.com"' in response.body

        user_dict = tk.get_action('user_show')({
            'model': model, 'session': model.Session, 'user': 'testsysadmin'},
            {'id': 'sue@example.com'})
        test_client = self.get_backwards_compatible_test_client()
        params = _get_user_params(user_dict)
        params['email'] = 'EXISTING@example.com'
        auth = {'Authorization': str(sue_obj.apikey)}
        user_updated = test_client.post(url_for, data=params, extra_environ=auth)
        assert '<li data-field-label="Email">Email: The email address is already registered on HDX. Please use the sign in screen below.</li>' in user_updated.body

        user = model.Session.query(model.User).get(sue_user['id'])
        assert_equal(user.email, sue_user.get('email'))


class TestResetPasswordSendingEmail(hdx_test_base.HdxFunctionalBaseTest):
    @classmethod
    def setup_class(cls):
        super(TestResetPasswordSendingEmail, cls).setup_class()

    def setup(self):
        test_helpers.reset_db()
        test_helpers.search.clear_all()

    @pytest.mark.usefixtures("with_request_context")
    def test_send_reset_email(self, mail_server):
        '''Password reset email is sent for valid user email'''
        user = factories.User(name='sue', email='sue@example.com', password='abcdefgh', fullname='Sue Tester')
        user_obj = model.User.get(user.get('name'))
        msgs = mail_server.get_smtp_messages()
        assert msgs == []

        try:
            reset_password.create_reset_key(user_obj, 3)
            subject = u'HDX password reset'
            reset_link = urljoin(config.get('ckan.site_url'),
                                 h.url_for(controller='user', action='perform_reset', id=user_obj.id,
                                           key=user_obj.reset_key))

            email_data = {
                'user_fullname': user_obj.fullname,
                'user_reset_link': reset_link,
                'expiration_in_hours': 3,
            }
            hdx_mailer.mail_recipient([{'display_name': user_obj.fullname, 'email': user_obj.email}], subject,
                                      email_data, footer=user_obj.email,
                                      snippet='email/content/password_reset.html')

            # check it went to the mock smtp server
            msgs = mail_server.get_smtp_messages()
            assert True
        except Exception as ex:
            assert False


class TestPasswordReset(hdx_test_base.HdxFunctionalBaseTest):
    @classmethod
    def setup_class(cls):
        super(TestPasswordReset, cls).setup_class()

    def setup(self):
        test_helpers.reset_db()
        test_helpers.search.clear_all()

    @pytest.mark.usefixtures("with_request_context")
    def test_send_reset_email_for_username(self, mail_server):
        '''Password reset email is sent for valid user username'''

        user = factories.User(name='sue', email='sue@example.com', password='abcdefgh', fullname='Sue Tester')
        # user_obj = model.User.get(user.get('name'))

        # send email
        url = h.url_for(controller='ckanext.hdx_users.controllers.mail_validation_controller:ValidationController',
                        action='request_reset')
        params = {
            'user': user.get('name')
        }

        # no emails sent yet
        msgs = mail_server.get_smtp_messages()
        assert_equal(len(msgs), 0)

        test_client = self.get_backwards_compatible_test_client()
        try:
            result = test_client.post(url, data=params)
            res = json.loads(result.body)
            assert_true(res['success'])
        except Exception as ex:
            assert False

        # an email has been sent
        msgs = mail_server.get_smtp_messages()
        assert_equal(len(msgs), 1)

        # check it went to the mock smtp server
        msg = msgs[0]
        assert_equal(msg[1], 'hdx@humdata.org')
        assert_equal(msg[2], [user.get('email')])
        assert_true('HDX_password_reset' in msg[3])

    @pytest.mark.usefixtures("with_request_context")
    def test_send_reset_email_for_email(self, mail_server):
        '''Password reset email is sent for valid email'''

        user = factories.User(name='sue', email='sue@example.com', password='abcdefgh', fullname='Sue Tester')
        # user_obj = model.User.get(user.get('name'))

        # send email
        url = h.url_for(controller='ckanext.hdx_users.controllers.mail_validation_controller:ValidationController',
                        action='request_reset')
        params = {
            'user': user.get('email')
        }

        # no emails sent yet
        msgs = mail_server.get_smtp_messages()
        assert_equal(len(msgs), 0)

        test_client = self.get_backwards_compatible_test_client()
        try:
            result = test_client.post(url, data=params)
            res = json.loads(result.body)
            assert_true(res['success'])
        except Exception as ex:
            assert False

        # an email has been sent
        msgs = mail_server.get_smtp_messages()
        assert_equal(len(msgs), 1)

        # check it went to the mock smtp server
        msg = msgs[0]
        assert_equal(msg[1], 'hdx@humdata.org')
        assert_equal(msg[2], [user.get('email')])
        assert_true('HDX_password_reset' in msg[3])

    @pytest.mark.usefixtures("with_request_context")
    def test_send_reset_email_for_email_different_case(self, mail_server):
        '''Password reset email is sent for valid user email but with lowercase'''

        user = factories.User(name='sue', email='sue@example.com', password='abcdefgh', fullname='Sue Tester')
        # user_obj = model.User.get(user.get('name'))

        # send email
        url = h.url_for(controller='ckanext.hdx_users.controllers.mail_validation_controller:ValidationController',
                        action='request_reset')
        params = {
            'user': user.get('email').upper()
        }

        # no emails sent yet
        msgs = mail_server.get_smtp_messages()
        assert_equal(len(msgs), 0)

        test_client = self.get_backwards_compatible_test_client()
        try:
            result = test_client.post(url, data=params)
            res = json.loads(result.body)
            assert_true(res['success'])
        except Exception as ex:
            assert False

        # an email has been sent
        msgs = mail_server.get_smtp_messages()
        assert_equal(len(msgs), 1)

        # check it went to the mock smtp server
        msg = msgs[0]
        assert_equal(msg[1], 'hdx@humdata.org')
        assert_equal(msg[2], [user.get('email')])
        assert_true('HDX_password_reset' in msg[3])

    @pytest.mark.usefixtures("with_request_context")
    def test_send_reset_email_for_email_not_existing(self, mail_server):
        '''Password reset email is sent for not a valid user email'''

        user = factories.User(name='sue', email='sue@example.com', password='abcdefgh', fullname='Sue Tester')
        # user_obj = model.User.get(user.get('name'))

        # send email
        url = h.url_for(controller='ckanext.hdx_users.controllers.mail_validation_controller:ValidationController',
                        action='request_reset')
        params = {
            'user': "test" + user.get('email').upper()
        }

        # no emails sent yet
        msgs = mail_server.get_smtp_messages()
        assert_equal(len(msgs), 0)

        test_client = self.get_backwards_compatible_test_client()
        try:
            result = test_client.post(url, data=params)
            res = json.loads(result.body)
            assert_false(res['success'])
        except Exception as ex:
            assert False

        # no email has been sent
        msgs = mail_server.get_smtp_messages()
        assert_equal(len(msgs), 0)


        # TODO create user according to the last onboarding. Note CAPTCHA!
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
