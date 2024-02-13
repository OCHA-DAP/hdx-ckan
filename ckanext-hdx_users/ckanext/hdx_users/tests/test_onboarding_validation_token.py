import pytest
import mock

import ckan.plugins.toolkit as tk

import ckanext.hdx_users.helpers.tokens as tokens


_get_action = tk.get_action
h = tk.h
@pytest.mark.usefixtures('clean_db', 'clean_index', 'with_request_context')
@mock.patch('ckanext.hdx_users.helpers.tokens.send_validation_email')
def test_validation_token(mock_send_validation_email, app):
    user_detail_url = h.url_for('hdx_user_onboarding.user-info')
    post_dict = {
        'fullname': 'Test User',
        'email': 'test@test.ttt',
        'email2': 'test@test.ttt',
        'name': 'test_user',
        'password1': 'Best_password_ever.0',
        'password2': 'Best_password_ever.0',
        'user_info_accept_terms': '',
    }
    user_detail_result = app.post(user_detail_url, data=post_dict)
    assert user_detail_result.status_code == 200
    assert mock_send_validation_email.call_count == 1

    token = mock_send_validation_email.call_args[0][1]['token']

    user_dict_before_validation = _get_action('user_show')({}, {'id': 'test_user'})
    token_dict_before_validation = tokens.token_show({'ignore_auth': True}, user_dict_before_validation)
    assert user_dict_before_validation['state'] == 'pending'
    assert token_dict_before_validation['valid'] == False

    first_char = 'b' if token[0] == 'a' else 'a'
    fake_token1 = first_char + token[1:]
    fake_token1_response = app.get(h.url_for('hdx_user_onboarding.validate_account', token=fake_token1))
    assert fake_token1_response.status_code == 404

    first_char = 'b' if token[0] == 'a' else 'a'
    fake_token1 = first_char + token[1:]
    fake_token1_response = app.get(h.url_for('hdx_user_onboarding.validate_account', token=fake_token1))
    assert fake_token1_response.status_code == 404

    account_validation_url = h.url_for('hdx_user_onboarding.validate_account', token=token)
    account_validation_response = app.get(account_validation_url)
    assert account_validation_response.status_code == 200
    user_dict_after_validation = _get_action('user_show')({}, {'id': 'test_user'})
    token_dict_after_validation = tokens.token_show({'ignore_auth': True}, user_dict_after_validation)
    assert user_dict_after_validation['state'] == 'active'
    assert token_dict_after_validation['valid'] == True

