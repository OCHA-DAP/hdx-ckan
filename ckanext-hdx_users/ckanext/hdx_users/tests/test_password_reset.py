import mock

from datetime import datetime, timedelta

import ckan.tests.factories as factories
import ckan.lib.mailer as ckan_mailer
import ckan.model as model
import ckan.plugins.toolkit as tk

import ckanext.hdx_theme.tests.hdx_test_base as hdx_test_base
import ckanext.hdx_users.helpers.reset_password as reset_password

_get_action = tk.get_action
NotAuthorized = tk.NotAuthorized
url_for = tk.url_for


class TestPasswordReset(hdx_test_base.HdxBaseTest):

    def test_old_style_reset_key_is_invalid(self):
        '''
        Tests that the old style reset keys that didn't contain an expiration date no longer work
        '''
        user_dict = factories.User(name='old_reset_key_user', email='old_reset_key_user@hdx.hdxtest.org')
        user = model.User.get(user_dict['id'])

        ckan_mailer.create_reset_key(user)

        assert user.reset_key

        reset_key_helper = reset_password.ResetKeyHelper(user.reset_key)

        assert not reset_key_helper.contains_expiration_time(), \
            'Keys created by core ckan should be recognized as not containing the time'

        assert reset_key_helper.is_expired(), 'Keys that have no time are considered expired'

    def test_new_style_reset_key_is_valid(self):
        '''
        Tests that the new style reset keys that contain an expiration date work
        '''
        user_dict = factories.User(name='new_reset_key_user', email='new_reset_key_user@hdx.hdxtest.org')
        user = model.User.get(user_dict['id'])

        reset_password.create_reset_key(user)

        assert user.reset_key

        reset_key_helper = reset_password.ResetKeyHelper(user.reset_key)

        assert reset_key_helper.contains_expiration_time()
        assert not reset_key_helper.is_expired()

    @mock.patch('ckanext.hdx_users.actions.update.hdx_mailer.mail_recipient')
    def test_password_reset_works(self, mocked_mail_recipient):
        email = 'password_reset_works_user@hdx.hdxtest.org'
        user_dict = factories.User(name='password_reset_works_user', email=email)

        data_dict = {
            'id': email
        }
        _get_action('hdx_send_reset_link')({}, data_dict)
        user = model.User.get(user_dict['id'])
        original_password = user.password

        context = {
            'user': user.id
        }

        user_dict['reset_key'] = user.reset_key
        user_dict['password'] = 'dummy_password'
        _get_action('user_update')(context, user_dict)
        user = model.User.get(user_dict['id'])
        assert original_password != user.password, 'Password should have been changed'

    @mock.patch('ckanext.hdx_users.actions.update.hdx_mailer.mail_recipient')
    def test_password_reset_fails_when_key_expired(self, mocked_mail_recipient):
        email = 'password_reset_fails_user@hdx.hdxtest.org'
        user_dict = factories.User(name='password_reset_fails_user', email=email)

        data_dict = {
            'id': email
        }
        _get_action('hdx_send_reset_link')({}, data_dict)
        user = model.User.get(user_dict['id'])
        original_password = user.password

        expired_time = (datetime.utcnow() - timedelta(days=1)).isoformat()
        key_random_part = user.reset_key.split('__')[0]
        expired_key = '{}__{}'.format(key_random_part, expired_time)
        user.reset_key = expired_key
        model.repo.commit()

        context = {
            'user': user.id
        }

        user_dict['reset_key'] = user.reset_key
        user_dict['password'] = 'dummy_password'
        try:
            _get_action('user_update')(context, user_dict)
            assert False
        except NotAuthorized as e:
            assert True, 'Password reset should not be possible with expired key'

    @mock.patch('ckanext.hdx_users.actions.update.hdx_mailer.mail_recipient')
    def test_reset_page_controller(self, mocked_mail_recipient):
        email = 'controller_password_reset_fails_user@hdx.hdxtest.org'
        user_dict = factories.User(name='controller_password_reset_fails_user', email=email)

        data_dict = {
            'id': email
        }
        _get_action('hdx_send_reset_link')({}, data_dict)
        user = model.User.get(user_dict['id'])

        expired_time = (datetime.utcnow() - timedelta(days=1)).isoformat()
        key_random_part = user.reset_key.split('__')[0]
        expired_key = '{}__{}'.format(key_random_part, expired_time)
        user.reset_key = expired_key
        model.repo.commit()

        reset_page_url = url_for('hdx_user.perform_reset', id=user.id, key=expired_key)
        response = self.app.get(reset_page_url)
        assert 'has expired' in response.html.text
