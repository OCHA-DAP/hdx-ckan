import pytest
import pyotp
import mock
import json

import ckan.plugins.toolkit as tk
import ckan.tests.factories as factories

from mock.mock import MagicMock

from ckanext.security.model import SecurityTOTP
from ckan.tests.helpers import CKANTestApp


_THROTTLE_MAP = {}

@pytest.mark.usefixtures('clean_db', 'clean_index', 'with_request_context')
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

    totp = _enable_totp(username)

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

@pytest.mark.usefixtures('clean_db', 'clean_index', 'with_request_context')
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

def _locked_out(username: str, app: CKANTestApp) -> bool:
    lockout_url = tk.h.url_for('hdx_user_autocomplete.check_lockout', user=username)
    response = app.get(lockout_url)
    if response.status_code != 200:
        raise Exception('Bad HTTP response' + response.status_code)
    reponse_dict = json.loads(response.body)
    return reponse_dict.get('result')
