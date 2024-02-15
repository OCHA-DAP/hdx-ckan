from typing import Dict

from werkzeug.test import TestResponse

import ckan.plugins.toolkit as tk
from ckan.tests.helpers import CKANTestApp

_get_action = tk.get_action
h = tk.h


USERNAME = 'test_user'
PASSWORD = 'Best_password_ever0'
FULLNAME = 'Test User'


def _apply_for_user_account(app: CKANTestApp, additional_params: Dict = None) -> TestResponse:
    user_detail_url = h.url_for('hdx_user_onboarding.user-info')
    post_dict = {
        'fullname': FULLNAME,
        'email': 'test@test.ttt',
        'email2': 'test@test.ttt',
        'name': USERNAME,
        'password1': PASSWORD,
        'password2': PASSWORD,
        'user_info_accept_terms': '',
    }
    if additional_params:
        post_dict.update(additional_params)
    user_detail_result = app.post(user_detail_url, data=post_dict)
    return user_detail_result

def _validate_account(app: CKANTestApp, token: str) -> TestResponse:
    return app.get(h.url_for('hdx_user_onboarding.validate_account', token=token))

def _attempt_login(app, follow_redirects=True):
    login_url = h.url_for('user.login')
    post_dict = {
        'login': USERNAME,
        'password': PASSWORD,
        'mfa': ''
    }
    login_response = app.post(login_url, data=post_dict, follow_redirects=follow_redirects)
    return login_response
