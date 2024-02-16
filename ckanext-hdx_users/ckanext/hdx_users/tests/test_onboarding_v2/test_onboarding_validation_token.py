import mock
import pytest
from mock.mock import MagicMock

import ckan.plugins.toolkit as tk
import ckan.model as model

import ckanext.hdx_users.helpers.tokens as tokens
import ckanext.hdx_users.model as umodel

from ckan.tests.helpers import CKANTestApp
from ckanext.hdx_users.helpers.reset_password import make_key

from ckanext.hdx_users.tests.test_onboarding_v2.helper import (
    _apply_for_user_account,
    _validate_account,
    _attempt_login,
    USERNAME,
    FULLNAME
)

_get_action = tk.get_action
h = tk.h



@pytest.mark.usefixtures('clean_db', 'clean_index', 'with_request_context')
@mock.patch('ckanext.hdx_users.helpers.tokens.send_validation_email')
def test_validation_token(mock_send_validation_email: MagicMock, app):
    user_detail_result = _apply_for_user_account(app)
    assert user_detail_result.status_code == 200
    assert mock_send_validation_email.call_count == 1

    token = mock_send_validation_email.call_args[0][1]['token']

    user_dict_before_validation = _get_action('user_show')({}, {'id': 'test_user'})
    token_dict_before_validation = tokens.token_show({'ignore_auth': True}, user_dict_before_validation)
    assert user_dict_before_validation['state'] == 'pending'
    assert token_dict_before_validation['valid'] == False

    first_char = 'b' if token[0] == 'a' else 'a'
    fake_token1 = first_char + token[1:]
    fake_token1_response = _validate_account(app, fake_token1)
    assert fake_token1_response.status_code == 404

    account_validation_response = _validate_account(app, token)
    assert account_validation_response.status_code == 200
    user_dict_after_validation = _get_action('user_show')({}, {'id': 'test_user'})
    token_dict_after_validation = tokens.token_show({'ignore_auth': True}, user_dict_after_validation)
    assert user_dict_after_validation['state'] == 'active'
    assert token_dict_after_validation['valid'] == True


@pytest.mark.usefixtures('clean_db', 'clean_index', 'with_request_context')
@mock.patch('ckanext.hdx_users.helpers.tokens.send_validation_email')
def test_validation_token_expiration(mock_send_validation_email: MagicMock, app):
    user_detail_result = _apply_for_user_account(app)
    assert user_detail_result.status_code == 200

    initial_token = mock_send_validation_email.call_args[0][1]['token']
    token_obj = umodel.ValidationToken.get_by_token(initial_token)
    user_id = token_obj.user_id

    expired_token = make_key(-5) # create a key that expired already 5 mins ago
    token_obj.token = expired_token
    model.Session.commit()

    expired_token_response = _validate_account(app, expired_token)
    assert expired_token_response.status_code == 404

    initial_token_response = _validate_account(app, initial_token)
    assert initial_token_response.status_code == 404

    token_obj = umodel.ValidationToken.get(user_id=user_id)
    token_obj.token = initial_token
    model.Session.commit()

    expired_token_response = _validate_account(app, expired_token)
    assert expired_token_response.status_code == 404

    initial_token_response = _validate_account(app, initial_token)
    assert initial_token_response.status_code == 200




@pytest.mark.usefixtures('clean_db', 'clean_index', 'with_request_context')
@pytest.mark.ckan_config('ckanext.security.brute_force_key', 'user_name')
@mock.patch('ckanext.security.authenticator.LoginThrottle')
@mock.patch('ckanext.hdx_users.views.onboarding.send_username_confirmation_email')
@mock.patch('ckanext.hdx_users.helpers.tokens.send_validation_email')
def test_user_login(mock_send_validation_email: MagicMock, mock_send_username_confirmation_email: MagicMock,
                    MockLoginThrottle: MagicMock, app: CKANTestApp):
    '''
    Some unusual config changes and mocks are used here to go around the brute force protection logic from
    ckanext.security:
    -  The simulated test HTTP requests don't have an IP address, so we tell the security plugin to use the
       username instead for counting failed login attempts (hence the `ckanext.security.brute_force_key` config change)
    -  We don't have redis when running the tests. So the security plugin cannot store the information about how many
       failed login attempts there are per username. That's why we mock the
       `ckanext.security.authenticator.LoginThrottle` class and it's `is_locked` method.
    '''
    MockLoginThrottle.return_value.is_locked.return_value = False
    user_detail_result = _apply_for_user_account(app)
    assert mock_send_username_confirmation_email.call_count == 0

    login_response_before_validation = _attempt_login(app)
    assert 'Login failed' in login_response_before_validation

    token = mock_send_validation_email.call_args[0][1]['token']
    _validate_account(app, token)
    assert mock_send_username_confirmation_email.call_count == 1
    _get_action('user_show')({}, {'id': USERNAME})

    login_response_after_validation = _attempt_login(app)
    assert FULLNAME in login_response_after_validation


