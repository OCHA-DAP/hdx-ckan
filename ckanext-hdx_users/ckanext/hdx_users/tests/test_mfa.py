import pytest
import pyotp
import mock

import ckan.plugins.toolkit as tk
import ckan.tests.factories as factories

from mock.mock import MagicMock

from ckanext.security.model import SecurityTOTP
from ckan.tests.helpers import CKANTestApp


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
