import pytest
import mock
import datetime

import ckan.model as model
import ckan.plugins.toolkit as tk
import ckan.tests.factories as factories
import ckan.tests.helpers as helpers
from ckanext.hdx_users.helpers.permissions import Permissions
from ckanext.hdx_users.helpers.token_expiration_helper import get_expiration

_get_action = tk.get_action
NotAuthorized = tk.NotAuthorized


@pytest.mark.usefixtures('keep_db_tables_on_clean', 'clean_db', 'with_request_context')
class TestApiTokenExpirationEmail(object):
    EXPIRES_DAYS = 6  # days

    SYSADMIN_EMAIL = 'token_sysadmin@test.org'
    USER1_EMAIL = 'token_testuser1@test.org'
    USER2_EMAIL = 'token_testuser2@test.org'

    @mock.patch('ckanext.hdx_theme.plugin.send_email_on_token_creation')
    @mock.patch('ckanext.hdx_users.helpers.token_expiration_helper._mail_recipient')
    def test_notify_users_about_api_token_expiration(self, mail_recipient_mock, send_email_helper_mock):
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

        token_owner1 = factories.User(name='testuser1', email=self.USER1_EMAIL)
        context_owner1 = {
            'model': model,
            'user': token_owner1['name']
        }

        token_owner2 = factories.User(name='testuser2', email=self.USER2_EMAIL)
        context_owner2 = {
            'model': model,
            'user': token_owner1['name']
        }

        helpers.call_action('api_token_create', context=context_sysadmin, user=sysadmin['name'], name='token-sys-1',
                            expires_in=self.EXPIRES_DAYS, unit=24 * 60 * 60)

        helpers.call_action('api_token_create', context=context_owner1, user=token_owner1['name'], name='token-u1-1',
                            expires_in=self.EXPIRES_DAYS, unit=24 * 60 * 60)
        helpers.call_action('api_token_create', context=context_owner1, user=token_owner1['name'], name='token-u1-2',
                            expires_in=self.EXPIRES_DAYS + 1, unit=24 * 60 * 60)

        helpers.call_action('api_token_create', context=context_owner2, user=token_owner2['name'], name='token-u2-1',
                            expires_in=self.EXPIRES_DAYS - 2, unit=24 * 60 * 60)
        helpers.call_action('api_token_create', context=context_owner2, user=token_owner2['name'], name='token-u2-2',
                            expires_in=self.EXPIRES_DAYS + 2, unit=24 * 60 * 60)

        result = _get_action('notify_users_about_api_token_expiration')(context_sysadmin, {
            'days_in_advance': self.EXPIRES_DAYS,
            'expires_on_specified_day': True,
        })
        period_start_date = result['start_date']
        period_end_date = result['end_date']
        assert _difference_in_days(period_start_date, period_end_date) == 1

        expirations = (get_expiration(token)[:10] for token in model.Session.query(model.ApiToken).all())

        total_expired = len([exp for exp in expirations if period_start_date <= exp < period_end_date])

        assert mail_recipient_mock.call_count == total_expired
        email_addresses = (self.SYSADMIN_EMAIL, self.USER1_EMAIL)
        for call in mail_recipient_mock.call_args_list:
            email = call[0][1]
            assert email in email_addresses

        mail_recipient_mock.reset_mock()

        result = _get_action('notify_users_about_api_token_expiration')(context_sysadmin, {
            'days_in_advance': self.EXPIRES_DAYS,
            'expires_on_specified_day': False,
        })
        period_start_date = result['start_date']
        period_end_date = result['end_date']
        assert _difference_in_days(period_start_date, period_end_date) == self.EXPIRES_DAYS + 1
        email_bodies = (call[1]['body_html'] for call in mail_recipient_mock.call_args_list)
        token_in_email_count = len([email for email in email_bodies if 'token-u2-1' in email])
        assert token_in_email_count == 1, 'token-u2-1 need to appear in one email'

    @mock.patch('ckanext.hdx_theme.plugin.send_email_on_token_creation')
    @mock.patch('ckanext.hdx_users.helpers.token_expiration_helper._mail_recipient')
    def test_notify_users_about_api_token_expiration_permission(self, mail_recipient_mock, send_email_helper_mock):
        normal_user = factories.User(name='testuser1', email=self.USER1_EMAIL)
        context_owner1 = {
            'model': model,
            'user': normal_user['name']
        }

        try:
            _get_action('notify_users_about_api_token_expiration')(context_owner1, {
                'days_in_advance': self.EXPIRES_DAYS,
                'expires_on_specified_day': False,
            })
            assert False, 'User is not yet authorized to run expiration check.'
        except NotAuthorized as e:
            assert True

        context_for_permission_set = {
            'model': model,
            'user': normal_user['name'],
            'ignore_auth': True,
        }
        Permissions(normal_user['name']).set_permissions(context_for_permission_set,
                                                         [Permissions.PERMISSION_MANAGE_BASIC_SCHEDULED_TASKS])
        _get_action('notify_users_about_api_token_expiration')(context_owner1, {
            'days_in_advance': self.EXPIRES_DAYS,
            'expires_on_specified_day': False,
        })
        assert True, 'User should now be authorized to run expiration check.'


def _difference_in_days(start, end):
    start_date = datetime.datetime.strptime(start, "%Y-%m-%d")
    end_date = datetime.datetime.strptime(end, "%Y-%m-%d")
    diff = end_date - start_date
    return diff.days
