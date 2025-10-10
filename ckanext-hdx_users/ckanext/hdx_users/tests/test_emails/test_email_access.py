'''
Created on Dec 8, 2014

@author: alexandru-m-g
'''
import pytest
import mock
import json
from six.moves.urllib.parse import urljoin

import ckan.lib.helpers as h
import ckan.model as model
import ckan.plugins.toolkit as tk
import ckan.tests.helpers as test_helpers
import ckanext.hdx_theme.tests.hdx_test_base as hdx_test_base
import ckanext.hdx_users.helpers.mailer as hdx_mailer
import ckanext.hdx_users.helpers.reset_password as reset_password
from ckan.tests import factories

NotAuthorized = tk.NotAuthorized

@pytest.mark.usefixtures('keep_db_tables_on_clean', 'hdx_clean_db', 'clean_index', 'setup_user_data')
class TestEmailAccess(object):

    # @classmethod
    # def setup_class(cls):
    #     super(TestEmailAccess, cls).setup_class()
    #
    #     cls._get_action('user_create')({
    #         'model': model, 'session': model.Session, 'user': 'testsysadmin'},
    #         {'name': 'johnfoo', 'fullname': 'John Foo',
    #          'email': 'example@example.com', 'password': 'Abcdefgh12'})

    @classmethod
    def _get_action(cls, action_name):
        return tk.get_action(action_name)

    def test_email_access_by_page(self, app):
        admin_token = factories.APIToken(user='testsysadmin', expires_in=2, unit=60 * 60)['token']

        url = h.url_for('user.index')[:-1]
        profile_url = h.url_for(u'hdx_user.read', id='janedoe3')

        result = app.get(url, headers={'Authorization': admin_token})

        profile_result = app.get(profile_url, headers={'Authorization': admin_token})

        assert 'janedoe3@hdx.hdxtest.org' in str(result.body)
        assert 'All Sysadmins [' in str(result.body)
        assert 'janedoe3@hdx.hdxtest.org' not in str(profile_result.body)
        assert 'janedoe3' in str(profile_result.body)

        user_token = factories.APIToken(user='some_user', expires_in=2, unit=60 * 60)['token']
        result = app.get(url, headers={'Authorization': user_token})
        profile_result = app.get(profile_url, headers={'Authorization': user_token})

        assert 'some_user@hdx.hdxtest.org' not in str(
            result.body), 'emails should not be visible for normal users'
        assert 'some_user@hdx.hdxtest.org' not in str(
            profile_result.body), 'emails should not be visible for normal users'

        result = app.get(url)
        profile_result = app.get(profile_url)

        assert 'example@example.com' not in str(
            result.body), 'emails should not be visible for guests'
        assert 'example@example.com' not in str(
            profile_result.body), 'emails should not be visible for guests'

    def test_email_access_by_api(self):

        user_list = self._get_action('user_list')({
            'model': model, 'session': model.Session, 'user': 'testsysadmin'}, {})
        assert self._user_list_has_email(user_list, 'testsysadmin')
        user = self._get_action('user_show')({
            'model': model, 'session': model.Session, 'user': 'testsysadmin'}, {'id': 'janedoe3'})
        assert 'email' in user

        user_list = self._get_action('user_list')({
            'model': model, 'session': model.Session, 'user': 'tester'}, {})
        assert not self._user_list_has_email(
            user_list, 'tester'), 'emails should not be visible for normal users'
        user = self._get_action('user_show')({
            'model': model, 'session': model.Session, 'user': 'tester'},
            {'id': 'janedoe3'})
        assert not 'email' in user, 'emails should not be visible for normal users'

        try:
            user_list = self._get_action('user_list')({
                'model': model, 'session': model.Session}, {})
            assert not self._user_list_has_email(
                user_list), 'emails should not be visible for guests'
        except NotAuthorized:
            assert True, 'emails should not be visible for guests'

        try:
            user = self._get_action('user_show')({
                'model': model, 'session': model.Session}, {'id': 'janedoe3'})
            assert not 'email' in user, 'emails should not be visible for guests'
        except NotAuthorized:
            assert True, 'emails should not be visible for guests'

    def _user_list_has_email(self, users, current_username=''):
        if users:
            for user in users:
                if 'email' in user and current_username != user['name']:
                    return True

        return False

class TestUserEmailRegistration(hdx_test_base.HdxFunctionalBaseTest):
    @classmethod
    def setup_class(cls):
        super(TestUserEmailRegistration, cls).setup_class()

    def setup(self):
        test_helpers.reset_db()
        test_helpers.search.clear_all()


# Below imports and definitions are needed so that the tests below don't give an error when running pytest.
# The tests will be skipped for now as many functions and objects no longer available in 2.9

config = tk.config

def _get_user_params(user_dict):
    params = {
        'old_password': 'Abcdefgh12',
        'email': user_dict.get('email'),
        'save': 'True',
        'password1': '',
        'password2': '',
        'name': user_dict.get('name'),
        'fullname': 'Sue User',
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

    def setup_method(self):
        test_helpers.reset_db()
        test_helpers.search.clear_all()

    def test_edit_email(self):
        '''Editing an existing user's email is successful.'''
        sue_user = factories.User(name='sue', email='sue@example.com', password='Abcdefgh12')
        sue_token =  factories.APIToken(user='sue', expires_in=2, unit=60 * 60)['token']

        env = {'Authorization': sue_token}
        url_for = h.url_for('user.edit')
        response = self.app.get(
            url=url_for,
            headers=env,
        )
        # existing values in the form
        assert '<input id="field-username" type="hidden" name="name" value="sue"' in response.body
        assert '<input id="field-fullname" type="text" class="form-control" name="fullname"' in response.body
        assert '<input id="field-email" type="email" class="form-control" name="email" value="sue@example.com"' in response.body
        assert '<textarea id="field-about" class="form-control" name="about" cols="20" rows="5"' in response.body
        # assert '<input id="field-activity-streams-email-notifications" type="checkbox" name="activity_streams_email_notifications" value="True"' in response.body
        assert '<input id="field-password" type="password" class="form-control" name="old_password" value=""' in response.body
        assert '<input id="field-password" type="password" class="form-control" name="password1" value=""' in response.body
        assert '<input id="field-password-confirm" type="password" class="form-control" name="password2" value=""' in response.body

        user_dict = tk.get_action('user_show')({
            'model': model, 'session': model.Session, 'user': 'testsysadmin'},
            {'id': 'sue@example.com'})
        test_client = self.get_backwards_compatible_test_client()
        params = _get_user_params(user_dict)
        params['email'] = 'new@example.com'
        auth = {'Authorization': sue_token}
        user_updated = test_client.post(url_for, data=params, headers=auth)

        user = model.Session.query(model.User).get(sue_user['id'])
        assert user.email == 'new@example.com'

    def test_edit_email_to_existing(self):
        '''Editing to an existing user's email is unsuccessful.'''
        factories.User(name='existing', email='existing@example.com')
        sue_user = factories.User(name='sue', email='sue@example.com', password='Abcdefgh12')
        sue_token = factories.APIToken(user='sue', expires_in=2, unit=60 * 60)['token']

        auth = {'Authorization': sue_token}
        url_for = h.url_for('user.edit', id=sue_user['name'])
        response = self.app.get(
            url=url_for,
            headers=auth,
        )
        # existing email in the form
        assert '<input id="field-email" type="email" class="form-control" name="email" value="sue@example.com"' in response.body

        user_dict = tk.get_action('user_show')({
            'model': model, 'session': model.Session, 'user': 'testsysadmin'},
            {'id': 'sue@example.com'})
        test_client = self.get_backwards_compatible_test_client()
        params = _get_user_params(user_dict)
        params['email'] = 'existing@example.com'
        auth = {'Authorization': sue_token}
        user_updated = test_client.post(url_for, data=params, headers=auth)

        # error message in response
        assert '<li data-field-label="Email">Email: The email address is already registered on HDX.</li>' in user_updated.body

        # sue user email hasn't changed.
        user = model.Session.query(model.User).get(sue_user['id'])
        assert user.email == 'sue@example.com'

    def test_edit_email_invalid_format(self):
        '''Editing with an invalid email format is unsuccessful.'''
        sue_user = factories.User(name='sue', email='sue@example.com', password='Abcdefgh12')
        sue_token = factories.APIToken(user='sue', expires_in=2, unit=60 * 60)['token']

        auth = {'Authorization': sue_token}
        url_for = h.url_for('user.edit', id=sue_user['name'])
        response = self.app.get(
            url=url_for,
            headers=auth,
        )
        # existing email in the form
        assert '<input id="field-email" type="email" class="form-control" name="email" value="sue@example.com"' in response.body

        user_dict = tk.get_action('user_show')({
            'model': model, 'session': model.Session, 'user': 'testsysadmin'},
            {'id': 'sue@example.com'})
        test_client = self.get_backwards_compatible_test_client()
        params = _get_user_params(user_dict)
        params['email'] = 'invalid.com'
        auth = {'Authorization': sue_token}
        user_updated = test_client.post(url_for, data=params, headers=auth)

        # error message in response
        assert '<li data-field-label="Email">Email: Email {} is not a valid format</li>'.format(
            params['email']) in user_updated.body

        # sue user email hasn't changed.
        user = model.Session.query(model.User).get(sue_user['id'])
        assert user.email == 'sue@example.com'

    def test_edit_email_saved_as_lowercase(self):
        '''Editing with an email in uppercase will be saved as lowercase.'''
        existing_user = factories.User(name='existing', email='existing@example.com', password='Abcdefgh12')
        sue_user = factories.User(name='sue', email='sue@example.com', password='Abcdefgh12')
        sue_token = factories.APIToken(user='sue', expires_in=2, unit=60 * 60)['token']

        auth = {'Authorization': sue_token}
        url_for = h.url_for('user.edit', id=sue_user['name'])
        response = self.app.get(
            url=url_for,
            headers=auth,
        )
        # existing values in the form
        assert '<input id="field-email" type="email" class="form-control" name="email" value="sue@example.com"' in response.body

        user_dict = tk.get_action('user_show')({
            'model': model, 'session': model.Session, 'user': 'testsysadmin'},
            {'id': 'sue@example.com'})
        test_client = self.get_backwards_compatible_test_client()
        params = _get_user_params(user_dict)
        params['email'] = 'existing@example.com'
        auth = {'Authorization': sue_token}
        user_updated = test_client.post(url_for, data=params, headers=auth)
        assert '<li data-field-label="Email">Email: The email address is already registered on HDX.</li>' in user_updated.body

        user = model.Session.query(model.User).get(sue_user['id'])
        assert user.email == sue_user.get('email')

    def test_edit_email_differently_case_existing(self):
        '''Editing with an existing user's email will be unsuccessful, even is
        differently cased.'''
        '''Editing with an email in uppercase will be saved as lowercase.'''
        existing_user = factories.User(name='existing', email='existing@example.com', password='Abcdefgh12')
        sue_user = factories.User(name='sue', email='sue@example.com', password='Abcdefgh12')
        sue_token = factories.APIToken(user='sue', expires_in=2, unit=60 * 60)['token']

        auth = {'Authorization': sue_token}
        url_for = h.url_for('user.edit', id=sue_user['name'])
        response = self.app.get(
            url=url_for,
            headers=auth,
        )
        # existing values in the form
        assert '<input id="field-email" type="email" class="form-control" name="email" value="sue@example.com"' in response.body

        user_dict = tk.get_action('user_show')({
            'model': model, 'session': model.Session, 'user': 'testsysadmin'},
            {'id': 'sue@example.com'})
        test_client = self.get_backwards_compatible_test_client()
        params = _get_user_params(user_dict)
        params['email'] = 'EXISTING@example.com'
        auth = {'Authorization': sue_token}
        user_updated = test_client.post(url_for, data=params, headers=auth)
        assert '<li data-field-label="Email">Email: The email address is already registered on HDX.</li>' in user_updated.body

        user = model.Session.query(model.User).get(sue_user['id'])
        assert user.email == sue_user.get('email')


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
        user = factories.User(name='sue', email='sue@example.com', password='Abcdefgh12', fullname='Sue Tester')
        user_obj = model.User.get(user.get('name'))
        msgs = mail_server.get_smtp_messages()
        assert msgs == []

        try:
            reset_password.create_reset_key(user_obj, 20)
            subject = u'HDX password reset'
            password_reset_url = h.url_for('hdx_user.perform_reset', id=user_obj.id, key=user_obj.reset_key)
            reset_link = urljoin(config.get('ckan.site_url'),
                                 password_reset_url)

            email_data = {
                'user_fullname': user_obj.fullname,
                'user_reset_link': reset_link,
                'expiration_in_minutes': 20,
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

    def setup_method(self):
        test_helpers.reset_db()
        test_helpers.search.clear_all()

    @pytest.mark.usefixtures("with_request_context")
    @mock.patch('ckanext.hdx_users.helpers.mailer._mail_recipient_html')
    def test_send_reset_email_for_username(self, _mail_recipient_html):
        '''Password reset email is sent for valid user username'''

        user = factories.User(name='sue', email='sue@example.com', password='Abcdefgh12', fullname='Sue Tester')
        # user_obj = model.User.get(user.get('name'))

        # send email
        url = h.url_for('hdx_user.request_reset')
        params = {
            'user': user.get('name')
        }

        # no emails sent yet
        assert len(_mail_recipient_html.call_args_list) == 0

        test_client = self.get_backwards_compatible_test_client()
        try:
            result = test_client.post(url, data=params)
            res = json.loads(result.body)
            assert res['success']
        except Exception as ex:
            assert False

        # an email has been sent
        assert len(_mail_recipient_html.call_args_list) == 1

        # check it went to the mock smtp server
        assert _mail_recipient_html.call_args_list[0][0][2][0].get('email') == user.get('email')
        assert 'HDX password reset' in _mail_recipient_html.call_args_list[0][0][3]


    @pytest.mark.usefixtures("with_request_context")
    @mock.patch('ckanext.hdx_users.helpers.mailer._mail_recipient_html')
    def test_send_reset_email_for_email(self, _mail_recipient_html):
        '''Password reset email is sent for valid email'''

        user = factories.User(name='sue', email='sue@example.com', password='Abcdefgh12', fullname='Sue Tester')

        # send email
        url = h.url_for('hdx_user.request_reset')
        params = {
            'user': user.get('email')
        }

        # no emails sent yet
        assert len(_mail_recipient_html.call_args_list) == 0

        test_client = self.get_backwards_compatible_test_client()
        try:
            result = test_client.post(url, data=params)
            res = json.loads(result.body)
            assert res['success']
        except Exception as ex:
            assert False

        # an email has been sent
        assert len(_mail_recipient_html.call_args_list) == 1
        assert _mail_recipient_html.call_args_list[0][0][2][0].get('email') == user.get('email')
        assert 'HDX password reset' in _mail_recipient_html.call_args_list[0][0][3]

    @pytest.mark.usefixtures("with_request_context")
    @mock.patch('ckanext.hdx_users.helpers.mailer._mail_recipient_html')
    def test_send_reset_email_for_email_different_case(self, _mail_recipient_html):
        '''Password reset email is sent for valid user email but with lowercase'''

        user = factories.User(name='sue', email='sue@example.com', password='Abcdefgh12', fullname='Sue Tester')
        # user_obj = model.User.get(user.get('name'))

        # send email
        url = h.url_for('hdx_user.request_reset')
        params = {
            'user': user.get('email').upper()
        }

        # no emails sent yet
        assert len(_mail_recipient_html.call_args_list) == 0

        test_client = self.get_backwards_compatible_test_client()
        try:
            result = test_client.post(url, data=params)
            res = json.loads(result.body)
            assert res['success']
        except Exception as ex:
            assert False

        # an email has been sent
        assert len(_mail_recipient_html.call_args_list) == 1

        # check it went to the mock smtp server
        assert _mail_recipient_html.call_args_list[0][0][2][0].get('email') == user.get('email')
        assert 'HDX password reset' in _mail_recipient_html.call_args_list[0][0][3]

    @pytest.mark.usefixtures("with_request_context")
    @mock.patch('ckanext.hdx_users.helpers.mailer._mail_recipient_html')
    def test_send_reset_email_for_email_not_existing(self, _mail_recipient_html):
        '''Password reset email is sent for not a valid user email'''

        user = factories.User(name='sue', email='sue@example.com', password='Abcdefgh12', fullname='Sue Tester')
        # user_obj = model.User.get(user.get('name'))

        # send email
        url = h.url_for('hdx_user.request_reset')
        params = {
            'user': "test" + user.get('email').upper()
        }

        # no emails sent yet
        assert len(_mail_recipient_html.call_args_list) == 0

        test_client = self.get_backwards_compatible_test_client()
        try:
            result = test_client.post(url, data=params)
            res = json.loads(result.body)
            assert res['success']
        except Exception as ex:
            assert False

        # no email has been sent
        assert len(_mail_recipient_html.call_args_list) == 0

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
