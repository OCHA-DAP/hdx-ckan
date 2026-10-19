import pytest
import pyotp
import mock
import json
import time

import ckan.plugins.toolkit as tk
import ckan.tests.factories as factories

from mock.mock import MagicMock

from ckanext.security.model import SecurityTOTP
from ckan.tests.helpers import CKANTestApp, CKANResponse

_THROTTLE_MAP = {}

@pytest.mark.usefixtures('hdx_clean_db', 'clean_index', 'with_request_context')
@pytest.mark.ckan_config('ckanext.security.brute_force_key', 'user_name')
@mock.patch('ckanext.security.authenticator.LoginThrottle')
def test_mfa(MockLoginThrottle: MagicMock, app: CKANTestApp):
    MockLoginThrottle.return_value.is_locked.return_value = False
    username = 'test_user'
    email = 'test_user@test.test'
    fullname = 'Test User'
    password = 'Abcdefgh1-'
    factories.User(name=username, email=email, fullname=fullname, password=password)

    logged_in = _attempt_login(email, password + '!', '', fullname, app)
    assert not logged_in, 'Log in should not work with a wrong password'

    logged_in = _attempt_login(email, password, '', fullname, app)
    assert logged_in, 'Log in should work, mfa is not enabled'

    _logout(app)

    assert not _mfa_enabled(username, app)
    totp = _enable_totp(username)
    assert _mfa_enabled(username, app)
    assert _mfa_enabled(email, app)

    logged_in = _attempt_login(email, password, '', fullname, app)
    assert not logged_in, 'Log in should not work because mfa is enabled'

    code = totp.now()
    logged_in = _attempt_login(email, password + '!', code, fullname, app)
    assert not logged_in, 'Log in with mfa should not work because of wrong password'

    logged_in = _attempt_login(email, password, '111222', fullname, app)
    assert not logged_in, 'Log in with mfa should not work because of wrong mfa'

    code = totp.now()
    logged_in = _attempt_login(email, password, code, fullname, app)
    assert logged_in, 'Log in with mfa should work'

class MockedThrottleClient(object):
    prefix = 'mock'

    def __init__(self):
        self.client = _THROTTLE_MAP

    def get(self, key: str) -> str:
        return self.client.get(self.prefix + key)

    def set(self, key: str, value: str):
        self.client[self.prefix + key] = value

    def delete(self, key: str) -> str:
        return self.client.pop(self.prefix + key)

@pytest.mark.usefixtures('hdx_clean_db', 'clean_index', 'with_request_context')
@pytest.mark.ckan_config('ckanext.security.brute_force_key', 'user_name')
@mock.patch('ckanext.security.cache.login.ThrottleClient', new=MockedThrottleClient)
def test_lockout_by_throttle(app: CKANTestApp):
    username = 'test_user_lockout_by_throttle'
    fullname = 'Test Lockout'
    password = 'Abcdefgh1-'
    email = 'test_user_lockout_by_throttle@test.test'
    factories.User(name=username, email=email, fullname=fullname, password=password)

    # Non existent users cannot be locked out
    assert not _locked_out('non_existent_user', app)

    # Check that we can log in with the new user
    logged_in = _attempt_login(email, password, '', fullname, app)
    assert logged_in, 'Log in should work'

    # Check that new user is not locked. We're checking by email and username
    assert not _locked_out(username, app), 'user login should NOT be locked'
    assert not _locked_out(email, app), 'user login should NOT be locked'

    _logout(app)

    # Check that we can lock out the user if we try 10 times with wrong password.
    # Doesn't matter if we use email or username
    for i in range(0, 5):
        logged_in = _attempt_login(email, password + '!', '', fullname, app)
        assert not logged_in, 'Log in should not work with a wrong password'

    for i in range(0, 5):
        logged_in = _attempt_login(username, password + '!', '', fullname, app)
        assert not logged_in, 'Log in should not work with a wrong password'

    assert _locked_out(email, app), 'user login should be locked'
    assert _locked_out(username, app), 'user login should be locked'

    logged_in = _attempt_login(email, password, '', fullname, app)
    assert not logged_in, 'Log in should not work, user locked out'




def _enable_totp(username: str) -> pyotp.TOTP:
    security_challenge = SecurityTOTP.create_for_user(username)
    secret = security_challenge.secret
    totp = pyotp.TOTP(secret)
    return totp


def _attempt_login(username: str, password: str, mfa: str, success_string: str,
                   app: CKANTestApp, follow_redirects=True) -> bool:
    login_url = tk.h.url_for('user.login')
    post_dict = {
        'login': username,
        'password': password,
        'mfa': mfa,
    }
    login_response = app.post(login_url, data=post_dict, follow_redirects=follow_redirects)
    if 'Login failed' in login_response:
        return False
    elif success_string in login_response:
        return True
    raise Exception('We should never get here !')

def _logout(app: CKANTestApp) -> CKANResponse:
    logout_url = tk.h.url_for('user.logout')
    response = app.get(logout_url, follow_redirects=False)
    return response


def _locked_out(username: str, app: CKANTestApp) -> bool:
    lockout_url = tk.h.url_for('hdx_user_autocomplete.check_lockout', user=username)
    response = app.get(lockout_url)
    if response.status_code != 200:
        raise Exception('Bad HTTP response' + response.status_code)
    reponse_dict = json.loads(response.body)
    return reponse_dict.get('result')


def _mfa_enabled(username: str, app: CKANTestApp) -> bool:
    response = app.get(tk.h.url_for('hdx_user_autocomplete.check_mfa', user=username))
    return json.loads(response.body)['result']


def _auth(user_name: str) -> dict:
    return {'Authorization': factories.APIToken(user=user_name, expires_in=2, unit=60 * 60)['token']}


def _wrong_code(totp: pyotp.TOTP) -> str:
    now = time.time()
    valid_codes = {totp.at(now, offset) for offset in range(-2, 3)}
    return next(code for code in ('111222', '333444', '555666') if code not in valid_codes)


@pytest.mark.usefixtures('keep_db_tables_on_clean', 'hdx_clean_db')
@pytest.mark.ckan_config('hdx.security.site_name', 'HDX')
class TestTwoStepEndpoints(object):

    def test_delete(self, app: CKANTestApp):
        factories.User(name='mfa_owner_1')
        factories.User(name='mfa_other_1')
        factories.User(name='mfa_sysadmin_1', sysadmin=True)
        owner, other, sysadmin = _auth('mfa_owner_1'), _auth('mfa_other_1'), _auth('mfa_sysadmin_1')
        url = tk.h.url_for('hdx_user.delete', id='mfa_owner_1')
        SecurityTOTP.create_for_user('mfa_owner_1')

        assert app.post(url).status_code == 403
        assert app.get(url, headers=owner).status_code == 404
        assert app.post(url, headers=other).status_code == 403
        assert SecurityTOTP.get_for_user('mfa_owner_1') is not None

        assert app.post(url, headers=owner).status_code == 200
        assert SecurityTOTP.get_for_user('mfa_owner_1') is None

        SecurityTOTP.create_for_user('mfa_owner_1')
        assert app.post(url, headers=sysadmin).status_code == 200
        assert SecurityTOTP.get_for_user('mfa_owner_1') is None

        unknown_url = tk.h.url_for('hdx_user.delete', id='mfa_unknown_user')
        assert app.post(unknown_url, headers=sysadmin).status_code == 404

    def test_new(self, app: CKANTestApp):
        factories.User(name='mfa_owner_2')
        factories.User(name='mfa_other_2')
        factories.User(name='mfa_sysadmin_2', sysadmin=True)
        owner, other, sysadmin = _auth('mfa_owner_2'), _auth('mfa_other_2'), _auth('mfa_sysadmin_2')
        url = tk.h.url_for('hdx_user.new', id='mfa_owner_2')
        secret = SecurityTOTP.create_for_user('mfa_owner_2').secret

        assert app.get(url, headers=owner).status_code == 404
        assert app.post(url, headers=other).status_code == 403
        assert SecurityTOTP.get_for_user('mfa_owner_2').secret == secret

        res = app.post(url, headers=owner)
        assert res.status_code == 200
        new_secret = SecurityTOTP.get_for_user('mfa_owner_2').secret
        assert new_secret != secret
        assert new_secret in res.body

        assert app.post(url, headers=sysadmin).status_code == 200

    @pytest.mark.ckan_config('hdx.security.2fa.redirect', 'true')
    def test_configure_mfa(self, app: CKANTestApp):
        factories.User(name='mfa_owner_3')
        factories.User(name='mfa_other_3')
        factories.User(name='mfa_sysadmin_3', sysadmin=True)
        owner, other, sysadmin = _auth('mfa_owner_3'), _auth('mfa_other_3'), _auth('mfa_sysadmin_3')
        totp = pyotp.TOTP(SecurityTOTP.create_for_user('mfa_owner_3').secret)
        url = tk.h.url_for('hdx_user.configure_mfa', id='mfa_owner_3')

        assert app.post(url, data={'mfa': totp.now()}, headers=other).status_code == 403

        client = app.test_client()
        res = client.post(url, data={'mfa': _wrong_code(totp)}, headers=owner)
        assert '"success": false' in res.body
        res = client.get(tk.h.url_for('hdx_user.edit', id='mfa_owner_3'), headers=owner)
        assert 'Successfully configured and enabled the two-step verification.' not in res.body

        res = client.post(url, data={'mfa': totp.now()}, headers=owner)
        assert '"success": true' in res.body

        client = app.test_client()
        res = client.post(url, data={'mfa': totp.now()}, headers=sysadmin)
        assert '"success": true' in res.body
        res = client.get('/', headers=sysadmin, follow_redirects=False)
        assert res.status_code == 302
        assert 'show_totp' in res.headers['Location']

    def test_security_extension_routes(self, app: CKANTestApp):
        factories.User(name='mfa_owner_4')
        owner = _auth('mfa_owner_4')
        secret = SecurityTOTP.create_for_user('mfa_owner_4').secret

        assert app.get(tk.h.url_for('mfa_user.configure_mfa', id='mfa_owner_4'), headers=owner).status_code == 404
        assert app.get(tk.h.url_for('mfa_user.new', id='mfa_owner_4'), headers=owner).status_code == 404
        assert app.post(tk.h.url_for('mfa_user.new', id='mfa_owner_4'), headers=owner).status_code == 404
        login_data = {'login': 'mfa_owner_4', 'password': 'Abcdefgh1-', 'mfa': ''}
        assert app.post(tk.h.url_for('mfa_user.login'), data=login_data, headers=owner).status_code == 404
        assert SecurityTOTP.get_for_user('mfa_owner_4').secret == secret

    def test_edit_page(self, app: CKANTestApp):
        factories.User(name='mfa_owner_5')
        factories.User(name='mfa_sysadmin_5', sysadmin=True)
        secret = SecurityTOTP.create_for_user('mfa_owner_5').secret

        res = app.get(tk.h.url_for('hdx_user.edit', id='mfa_owner_5'), headers=_auth('mfa_sysadmin_5'))
        assert 'Two-step verification is on.' in res.body
        assert secret not in res.body

    @pytest.mark.ckan_config('hdx.security.2fa.redirect', 'true')
    def test_redirect_on_unmatched_routes(self, app: CKANTestApp):
        factories.User(name='mfa_sysadmin_6', sysadmin=True)
        sysadmin = _auth('mfa_sysadmin_6')

        assert app.post('/no-such-page/for-two-step-test', headers=sysadmin).status_code == 405
