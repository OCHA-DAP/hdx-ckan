'''
HDX-11757: CKAN core skips the CSRF check for every anonymous request and for requests with an API token
header, except on its own user.login and user.register (GHSA-3h7g-fpc6-9vc9). HDX serves login and signup from
its own views, which must still check the CSRF token.
'''
import mock
import pytest
from ckanext.hdx_theme.tests.hdx_test_util import post_with_csrf

import ckan.model as model
import ckan.plugins.toolkit as tk
import ckan.tests.factories as factories
from ckan.tests.helpers import CKANTestApp

h = tk.h

USERNAME = 'csrf_login_user'
EMAIL = 'csrf_login_user@test.test'
NEW_EMAIL = 'csrf_login_user_new@test.test'
PASSWORD = 'Abcdefgh1-'
OTHER_USERNAME = 'csrf_other_user'

LOGIN_URLS = ['/user/login', '/login', '/sign-in']


@pytest.fixture(autouse=True)
def close_db_session():
    yield
    # Tests below read the DB directly. Close that transaction, or the next test's hdx_users migration
    # (autouse migrate_hdx_users, DROP INDEX on "user") waits for its lock forever.
    model.Session.remove()


@pytest.fixture()
def setup_users():
    factories.User(name=USERNAME, email=EMAIL, fullname='CSRF Login User', password=PASSWORD)
    factories.User(name=OTHER_USERNAME, email='csrf_other_user@test.test')


def _login_data():
    return {'login': USERNAME, 'password': PASSWORD, 'mfa': ''}


def _signup_data():
    return {
        'fullname': 'CSRF Signup User',
        'email': 'csrf_signup_user@test.test',
        'email2': 'csrf_signup_user@test.test',
        'name': 'csrf_signup_user',
        'password1': PASSWORD,
        'password2': PASSWORD,
        'user_info_accept_terms': 'true',
    }


def _remember_cookie_set(response) -> bool:
    cookie_name = tk.config.get('REMEMBER_COOKIE_NAME')
    return any(c.startswith(cookie_name + '=') for c in response.headers.getlist('Set-Cookie'))


@pytest.mark.usefixtures('hdx_clean_db', 'setup_users')
class TestCsrfOnLoginAndSignup(object):

    @pytest.mark.parametrize('login_url', LOGIN_URLS)
    def test_login_without_csrf_token_is_rejected(self, app: CKANTestApp, login_url: str):
        response = app.post(login_url, data=_login_data(), follow_redirects=False)
        assert response.status_code == 400
        assert not _remember_cookie_set(response)

    def test_login_with_api_token_header_without_csrf_token_is_rejected(self, app: CKANTestApp):
        api_token = factories.APIToken(user=OTHER_USERNAME, expires_in=2, unit=60 * 60)['token']
        response = app.post('/user/login', data=_login_data(), headers={'Authorization': api_token},
                            follow_redirects=False)
        assert response.status_code == 400

    def test_login_with_wrong_csrf_token_is_rejected(self, app: CKANTestApp):
        data = dict(_login_data())
        data[tk.config.get('WTF_CSRF_FIELD_NAME')] = 'not-a-valid-token'
        response = app.post('/user/login', data=data, follow_redirects=False)
        assert response.status_code == 400

    @pytest.mark.parametrize('remember', [None, '63072000'])
    # the test client sends no REMOTE_ADDR, so ckanext-security can't build its default (IP) throttle key
    @pytest.mark.ckan_config('ckanext.security.brute_force_key', 'user_name')
    @mock.patch('ckanext.security.authenticator.LoginThrottle')
    def test_login_with_csrf_token_works(self, MockLoginThrottle, app: CKANTestApp, remember):
        # the throttle state lives in a cache shared across tests; keep it out of this test
        MockLoginThrottle.return_value.is_locked.return_value = False
        data = _login_data()
        if remember:
            data['remember'] = remember
        response = post_with_csrf(app, '/user/login', data=data, follow_redirects=False)
        assert response.status_code == 302, 'A successful login redirects'
        assert _remember_cookie_set(response) == bool(remember)

    # Flask-WTF's protect() ignores WTF_CSRF_ENABLED, so @enforce_csrf has to check it
    @pytest.mark.ckan_config('WTF_CSRF_ENABLED', False)
    @pytest.mark.ckan_config('ckanext.security.brute_force_key', 'user_name')
    @mock.patch('ckanext.security.authenticator.LoginThrottle')
    def test_login_without_csrf_token_works_when_csrf_is_disabled(self, MockLoginThrottle, app: CKANTestApp):
        MockLoginThrottle.return_value.is_locked.return_value = False
        response = app.post('/user/login', data=_login_data(), follow_redirects=False)
        assert response.status_code == 302, 'A successful login redirects'

    @mock.patch('ckanext.hdx_users.helpers.tokens.send_validation_email')
    def test_signup_without_csrf_token_is_rejected(self, mock_send_validation_email, app: CKANTestApp):
        url = h.url_for('hdx_user_onboarding.user-info')
        response = app.post(url, data=_signup_data(), follow_redirects=False)
        assert response.status_code == 400
        assert model.User.by_name('csrf_signup_user') is None
        assert not mock_send_validation_email.called

    @mock.patch('ckanext.hdx_users.helpers.tokens.send_validation_email')
    def test_signup_with_csrf_token_works(self, mock_send_validation_email, app: CKANTestApp):
        url = h.url_for('hdx_user_onboarding.user-info')
        response = post_with_csrf(app, url, data=_signup_data(), follow_redirects=False)
        assert response.status_code == 302
        assert model.User.by_name('csrf_signup_user').state == model.State.PENDING
        assert mock_send_validation_email.called

    @mock.patch('ckanext.hdx_users.views.onboarding._user_can_change_email')
    @mock.patch('ckanext.hdx_users.helpers.tokens.is_user_validated_and_token_disabled', return_value=False)
    def test_change_email_without_csrf_token_is_rejected(self, mock_is_user_validated,
                                                         mock_user_can_change_email, app: CKANTestApp):
        user = model.User.by_name(USERNAME)
        mock_user_can_change_email.return_value = user.id

        url = h.url_for('hdx_user_onboarding.change_email')
        response = app.post(url, data={'email': NEW_EMAIL, 'email2': NEW_EMAIL}, follow_redirects=False)
        assert response.status_code == 400
        model.Session.expire_all()
        assert model.User.by_name(USERNAME).email == EMAIL
