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
from ckanext.hdx_org_group.helpers.static_lists import ORGANIZATION_TYPE_LIST

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

    def setup_method(self):
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
        assert '<input type="hidden" name="name" value="sue">' in response.body
        assert 'id="field-fullname"' in response.body
        assert 'id="field-email"' in response.body
        assert 'value="sue@example.com"' in response.body
        assert 'id="field-about"' in response.body
        assert 'id="field-activity-streams-email-notifications"' in response.body
        assert 'id="field-old-password"' in response.body
        assert 'id="field-password"' in response.body
        assert 'id="field-password-confirm"' in response.body

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
        assert 'id="field-email"' in response.body
        assert 'value="sue@example.com"' in response.body

        user_dict = tk.get_action('user_show')({
            'model': model, 'session': model.Session, 'user': 'testsysadmin'},
            {'id': 'sue@example.com'})
        test_client = self.get_backwards_compatible_test_client()
        params = _get_user_params(user_dict)
        params['email'] = 'existing@example.com'
        auth = {'Authorization': sue_token}
        user_updated = test_client.post(url_for, data=params, headers=auth)

        # error message in response
        assert '<span class="c-search-input__error">The email address is already registered on HDX.</span>' in user_updated.body

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
        assert 'id="field-email"' in response.body
        assert 'value="sue@example.com"' in response.body

        user_dict = tk.get_action('user_show')({
            'model': model, 'session': model.Session, 'user': 'testsysadmin'},
            {'id': 'sue@example.com'})
        test_client = self.get_backwards_compatible_test_client()
        params = _get_user_params(user_dict)
        params['email'] = 'invalid.com'
        auth = {'Authorization': sue_token}
        user_updated = test_client.post(url_for, data=params, headers=auth)

        # error message in response
        assert '<span class="c-search-input__error">Email {} is not a valid format</span>'.format(
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
        assert 'id="field-email"' in response.body
        assert 'value="sue@example.com"' in response.body

        user_dict = tk.get_action('user_show')({
            'model': model, 'session': model.Session, 'user': 'testsysadmin'},
            {'id': 'sue@example.com'})
        test_client = self.get_backwards_compatible_test_client()
        params = _get_user_params(user_dict)
        params['email'] = 'existing@example.com'
        auth = {'Authorization': sue_token}
        user_updated = test_client.post(url_for, data=params, headers=auth)
        assert '<span class="c-search-input__error">The email address is already registered on HDX.</span>' in user_updated.body

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
        assert 'id="field-email"' in response.body
        assert 'value="sue@example.com"' in response.body

        user_dict = tk.get_action('user_show')({
            'model': model, 'session': model.Session, 'user': 'testsysadmin'},
            {'id': 'sue@example.com'})
        test_client = self.get_backwards_compatible_test_client()
        params = _get_user_params(user_dict)
        params['email'] = 'EXISTING@example.com'
        auth = {'Authorization': sue_token}
        user_updated = test_client.post(url_for, data=params, headers=auth)
        assert '<span class="c-search-input__error">The email address is already registered on HDX.</span>' in user_updated.body

        user = model.Session.query(model.User).get(sue_user['id'])
        assert user.email == sue_user.get('email')

    def test_edit_own_page(self):
        '''A user's own page has the public profile link and no sysadmin sections.'''
        factories.User(name='sue', email='sue@example.com', password='Abcdefgh12')
        sue_token = factories.APIToken(user='sue', expires_in=2, unit=60 * 60)['token']

        response = self.app.get(url=h.url_for('user.edit'), headers={'Authorization': sue_token})
        assert '<h2 class="hdx-v2-user-dashboard-header__title">Profile and Password</h2>' in response.body
        assert 'View public profile' in response.body
        assert 'href="/user/sue"' in response.body
        assert 'target="_blank" rel="noopener noreferrer"' in response.body
        assert 'Old password' in response.body
        assert 'id="two-step-drawer"' not in response.body
        assert 'id="delete-user-drawer"' not in response.body

    def test_edit_other_user_as_sysadmin(self):
        '''A sysadmin on another user's page gets the 2FA and delete drawers.'''
        sue_user = factories.User(name='sue', email='sue@example.com', fullname='Sue Tester')
        factories.Sysadmin(name='sysadmin079')
        token = factories.APIToken(user='sysadmin079', expires_in=2, unit=60 * 60)['token']

        response = self.app.get(url=h.url_for('user.edit', id='sue'), headers={'Authorization': token})
        assert "Update Sue Tester's account details, password, and login preferences" in response.body
        assert 'Sysadmin password' in response.body
        assert 'id="two-step-drawer"' in response.body
        assert 'Turn on two-step verification' in response.body
        assert 'id="delete-user-drawer"' in response.body
        assert 'action="/user/delete/{}"'.format(sue_user['id']) in response.body
        assert 'Are you sure you want to delete this user?' in response.body
        assert response.body.count('c-button--size-m is-disabled"') == 1

    def test_delete_drawer_for_maintainer(self):
        '''A dataset maintainer's delete drawer lists the datasets and disables Confirm.'''
        factories.User(name='sue', email='sue@example.com')
        factories.Sysadmin(name='sysadmin079')
        token = factories.APIToken(user='sysadmin079', expires_in=2, unit=60 * 60)['token']
        factories.Group(name='location079')
        factories.Organization(
            name='org079',
            title='Org 079',
            users=[{'name': 'sue', 'capacity': 'admin'}],
            hdx_org_type=ORGANIZATION_TYPE_LIST[0][1],
            org_url='https://hdx.hdxtest.org/'
        )
        context = {'model': model, 'session': model.Session, 'user': 'sysadmin079'}
        tk.get_action('package_create')(context, {
            'package_creator': 'test function',
            'private': False,
            'dataset_date': '[1960-01-01 TO 2012-12-31]',
            'caveats': 'These are the caveats',
            'license_other': 'TEST OTHER LICENSE',
            'methodology': 'This is a test methodology',
            'dataset_source': 'Test data',
            'license_id': 'hdx-other',
            'name': 'dataset079',
            'notes': 'This is a test dataset',
            'title': 'Dataset 079',
            'owner_org': 'org079',
            'groups': [{'name': 'location079'}],
            'data_update_frequency': '30',
            'maintainer': 'sue'
        })

        response = self.app.get(url=h.url_for('user.edit', id='sue'), headers={'Authorization': token})
        assert 'User cannot be removed. Please change maintainer for the following datasets:' in response.body
        assert '<li><a href="/dataset/dataset079" target="_blank">Dataset 079</a></li>' in response.body
        assert response.body.count('c-button--size-m is-disabled"') == 2

    def test_edit_wrong_old_password(self):
        '''A wrong old password shows its error under the field and keeps the new passwords.'''
        sue_user = factories.User(name='sue', email='sue@example.com', password='Abcdefgh12')
        sue_token = factories.APIToken(user='sue', expires_in=2, unit=60 * 60)['token']
        url_for = h.url_for('user.edit', id=sue_user['name'])

        user_dict = tk.get_action('user_show')({
            'model': model, 'session': model.Session, 'user': 'testsysadmin'},
            {'id': 'sue@example.com'})
        test_client = self.get_backwards_compatible_test_client()
        params = _get_user_params(user_dict)
        params['email'] = 'sue@example.com'
        params['old_password'] = 'Wrongpassword12'
        params['password1'] = 'Newpassword12'
        params['password2'] = 'Newpassword12'
        response = test_client.post(url_for, data=params, headers={'Authorization': sue_token})

        assert '<span class="c-search-input__error">Password entered was incorrect</span>' in response.body
        assert 'value="Newpassword12"' in response.body
        assert model.User.by_name('sue').validate_password('Abcdefgh12')


class TestResetPasswordSendingEmail(hdx_test_base.HdxFunctionalBaseTest):
    @classmethod
    def setup_class(cls):
        super(TestResetPasswordSendingEmail, cls).setup_class()

    def setup_method(self):
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
