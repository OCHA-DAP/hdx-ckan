import pytest
import mock

import ckan.model as model
import ckan.plugins.toolkit as tk
import ckan.tests.factories as factories
import ckan.tests.helpers as helpers

_get_action = tk.get_action
NotAuthorized = tk.NotAuthorized


@pytest.mark.usefixtures('keep_db_tables_on_clean', 'clean_db', 'with_request_context')
class TestApiTokenCreationEmail(object):

    SYSADMIN_EMAIL = 'token_sysadmin@test.org'
    USER_EMAIL = 'token_testuser@test.org'

    @mock.patch('ckanext.hdx_users.helpers.token_creation_notification_helper._mail_recipient')
    def test_notify_users_about_api_token_creation(self, mail_recipient_mock):
        '''
        :param mail_recipient_mock:
        :type mail_recipient_mock: mock.MagicMock
        :return:
        '''
        sysadmin = factories.Sysadmin(email=self.SYSADMIN_EMAIL)
        context_sysadmin = {
            'model': model,
            'user': sysadmin['name']
        }

        token_owner = factories.User(name='testuser', email=self.USER_EMAIL, fullname='Test User')
        context_owner = {
            'model': model,
            'user': token_owner['name']
        }

        helpers.call_action('api_token_create', context=context_sysadmin, user=token_owner['name'], name='token-sys-1',
                            expires_in=5, unit=24 * 60 * 60)
        assert mail_recipient_mock.call_count == 1
        assert mail_recipient_mock.call_args[0][1] == self.USER_EMAIL

        helpers.call_action('api_token_create', context=context_owner, user=token_owner['name'], name='token-u1-1',
                            expires_in=5, unit=24 * 60 * 60)
        assert mail_recipient_mock.call_count == 2
        assert mail_recipient_mock.call_args[0][1] == self.USER_EMAIL
