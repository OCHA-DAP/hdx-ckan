import mock
import pytest

import ckan.model as model
import ckan.plugins.toolkit as tk
import ckan.tests.factories as factories
from ckanext.hdx_users.helpers.constants import ONBOARDING_CAME_FROM_EXTRAS_KEY, ONBOARDING_CAME_FROM_STATE_EXTRAS_KEY, \
    ONBOARDING_MAILCHIMP_OPTIN_KEY

_get_action = tk.get_action
h = tk.h

USER = 'onboarding_testuser'
USER_EMAIL = 'onboarding_testuser@test.org'

SYSADMIN = 'onboarding_sysadmin'
SYSADMIN_EMAIL = 'onboarding_sysadmin@test.org'

NEW_USER = 'onboarding_new_testuser'
NEW_USER_EMAIL = 'onboarding_new_testuser@test.org'

NEW_USER_2 = 'onboarding_new_testuser_2'
NEW_USER_EMAIL_2 = 'onboarding_new_testuser_2@test.org'

@pytest.fixture()
def setup_data():
    factories.Sysadmin(name=SYSADMIN, email=SYSADMIN_EMAIL, fullname='Sysadmin User')
    factories.User(name=USER, email=USER_EMAIL, fullname='Test User')


def _sysadmin_context():
    return {
        'model': model,
        'user': SYSADMIN
    }


def _user_context():
    return {
        'model': model,
        'user': USER
    }

def build_data_dict():
    data_dict = {
        'fullname': 'Onboarding User',
        'email': NEW_USER_EMAIL,
        'email2': NEW_USER_EMAIL,
        'name': NEW_USER,
        'password1': 'asdASD123!@#',
        'password2': 'asdASD123!@#',
        'user_info_accept_terms': 'true',
        'user_info_accept_emails': 'true'

    }
    return data_dict

@pytest.mark.usefixtures("clean_db", "clean_index", "setup_data")
class TestOnboarding(object):

    def test_value_proposition_page_load(self, app):
        sysadmin_token = factories.APIToken(user=SYSADMIN, expires_in=2, unit=60 * 60)['token']
        testuser_token = factories.APIToken(user=USER, expires_in=2, unit=60 * 60)['token']

        url = h.url_for('hdx_user_onboarding.value_proposition')
        result = app.get(url)
        assert '<title>Account options ' in result.body
        # this might change from translation
        assert 'HDX account options' in result.body
        assert 'href="/signup/user-info/"' in result.body

        result = app.get(url, extra_environ={'Authorization': testuser_token}, status=403)
        # if user is logged in, the page should not be visible
        assert result.status_code == 403

        result = app.get(url, extra_environ={'Authorization': sysadmin_token}, status=200)
        # if user is sysadmin, page can be displayed
        assert result.status_code == 200

    def test_signup_user_info_load(self, app):
        sysadmin_token = factories.APIToken(user=SYSADMIN, expires_in=2, unit=60 * 60)['token']
        testuser_token = factories.APIToken(user=USER, expires_in=2, unit=60 * 60)['token']

        url = h.url_for('hdx_user_onboarding.user-info')
        result = app.get(url)
        assert '<title>User info ' in result.body
        # this might change from translation
        assert 'name="fullname"' in result.body
        assert 'name="email"' in result.body
        assert 'name="email2"' in result.body
        assert 'name="name"' in result.body
        assert 'name="password1"' in result.body
        assert 'name="password2"' in result.body
        assert 'name="user_info_accept_terms"' in result.body
        assert 'name="user_info_accept_emails"' in result.body
        assert 'id="user-info-submit-button"' in result.body
        assert 'id="user-info-cancel-button"' in result.body

        result = app.get(url, extra_environ={'Authorization': testuser_token}, status=403)
        # if user is logged in, the page should not be visible
        assert result.status_code == 403

        result = app.get(url, extra_environ={'Authorization': sysadmin_token}, status=200)
        # if user is sysadmin, page can be displayed
        assert result.status_code == 200

    @mock.patch('ckanext.hdx_users.helpers.mailer._mail_recipient_html')
    def test_onboarding_create_user(self, _mail_recipient_html, app):
        data_dict = build_data_dict()

        url = h.url_for('hdx_user_onboarding.user-info')
        result = app.post(url, data=data_dict)
        assert result.status_code == 200
        assert NEW_USER_EMAIL in result.body
        assert '<div class="stepper__name">Personal details</div>' in result.body
        assert '<div class="stepper__name">Verify email</div>' in result.body
        assert '<div class="stepper__name">Account created</div>' in result.body

        assert len(_mail_recipient_html.call_args_list) == 1
        assert _mail_recipient_html.call_args_list[0][0][2][0].get('email') == NEW_USER_EMAIL

        user_dict = _get_action('user_show')(_sysadmin_context(), {'id': NEW_USER})
        assert NEW_USER == user_dict.get('name')
        assert NEW_USER_EMAIL == user_dict.get('email')
        assert 'pending' == user_dict.get('state')

        ue_user = _get_action('user_extra_value_by_keys_show')(_sysadmin_context(),
                                                               {
                                                                   'user_id': user_dict.get('id'),
                                                                   'keys': [ONBOARDING_CAME_FROM_EXTRAS_KEY,
                                                                            ONBOARDING_CAME_FROM_STATE_EXTRAS_KEY,
                                                                            ONBOARDING_MAILCHIMP_OPTIN_KEY]
                                                               }
                                                               )

        for ue in ue_user:
            if ue.get('key') == ONBOARDING_CAME_FROM_EXTRAS_KEY:
                assert ue.get('value') is None
            if ue.get('key') == ONBOARDING_CAME_FROM_STATE_EXTRAS_KEY:
                assert ue.get('value') == 'active'
            if ue.get('key') == ONBOARDING_MAILCHIMP_OPTIN_KEY:
                assert ue.get('value') == 'true'
        assert len(ue_user) == 3


    def test_onboarding_create_wrong_user(self, app):
        testuser_token = factories.APIToken(user=USER, expires_in=2, unit=60 * 60)['token']

        data_dict = {}
        url = h.url_for('hdx_user_onboarding.user-info')
        result = app.post(url, data=data_dict)
        assert result.status_code == 200
        assert 'The passwords you entered do not match' in result.body
        assert 'Missing value' in result.body

        data_dict = build_data_dict()
        data_dict['email2'] = USER_EMAIL

        result = app.post(url, data=data_dict)
        assert result.status_code == 200
        assert 'The emails you entered do not match' in result.body

        data_dict = build_data_dict()
        data_dict['password2'] = 'asdASD123!@#1'

        result = app.post(url, data=data_dict)
        assert result.status_code == 200
        assert 'The passwords you entered do not match' in result.body

        data_dict = build_data_dict()
        data_dict['name'] = USER

        result = app.post(url, data=data_dict)
        assert result.status_code == 200
        assert 'That login name is not available' in result.body

        data_dict = build_data_dict()

        auth = {'Authorization': testuser_token}
        result = app.post(url, data=data_dict, extra_environ=auth)
        assert result.status_code == 403
        assert 'Sorry, you don\'t have permission to access this page' in result.body


    def test_onboarding_create_user_if_pending(self, app):

        data_dict = build_data_dict()
        url = h.url_for('hdx_user_onboarding.user-info')
        result = app.post(url, data=data_dict)
        assert result.status_code == 200
        assert NEW_USER_EMAIL in result.body

        user_dict = _get_action('user_show')(_sysadmin_context(), {'id': NEW_USER})
        assert NEW_USER == user_dict.get('name')
        assert NEW_USER_EMAIL == user_dict.get('email')
        assert 'pending' == user_dict.get('state')

        data_dict['name'] = NEW_USER_2
        result = app.post(url, data=data_dict)
        assert result.status_code == 200
        assert NEW_USER_EMAIL in result.body

        user_dict = _get_action('user_show')(_sysadmin_context(), {'id': NEW_USER_2})
        assert NEW_USER_2 == user_dict.get('name')
        assert NEW_USER_EMAIL == user_dict.get('email')
        assert 'pending' == user_dict.get('state')

        user_dict = _get_action('user_show')(_sysadmin_context(), {'id': NEW_USER})
        assert NEW_USER == user_dict.get('name')
        assert NEW_USER_EMAIL == user_dict.get('email')
        assert 'pending' == user_dict.get('state')

    def test_delete_user(self, app):
        sysadmin_token = factories.APIToken(user=SYSADMIN, expires_in=2, unit=60 * 60)['token']
        testuser_token = factories.APIToken(user=USER, expires_in=2, unit=60 * 60)['token']

        data_dict = build_data_dict()
        url = h.url_for('hdx_user_onboarding.user-info')
        result = app.post(url, data=data_dict)
        assert result.status_code == 200
        assert NEW_USER_EMAIL in result.body

        user_dict = _get_action('user_show')(_sysadmin_context(), {'id': NEW_USER})
        delete_url = h.url_for('user.delete', id=user_dict.get('id'))
        auth_sysadmin = {'Authorization': sysadmin_token}
        result = app.post(delete_url, data={'id':user_dict.get('id')}, extra_environ=auth_sysadmin)

        profile_url = h.url_for(u'hdx_user.read', id=user_dict.get('id'))

        profile_result = app.get(profile_url, extra_environ=auth_sysadmin)
        assert '<span class="label label-important">Deleted</span>' in profile_result.body

        auth_testuser = {'Authorization': testuser_token}
        profile_result2 = app.get(profile_url, status=404, extra_environ=auth_testuser)
        assert '404' in profile_result2.status
