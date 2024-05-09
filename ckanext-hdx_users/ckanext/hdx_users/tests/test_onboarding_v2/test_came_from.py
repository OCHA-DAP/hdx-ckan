import json
from typing import Dict

import mock
import pytest
import ckan.plugins.toolkit as tk

from mock import MagicMock

from ckanext.hdx_users.helpers.constants import ONBOARDING_START_PAGE_HDX_CONNECT, \
    ONBOARDING_START_PAGE_CONTACT_CONTRIBUTOR, ONBOARDING_VALUE_PROPOSITION_INDIVIDUAL_ACCOUNT, \
    ONBOARDING_VALUE_PROPOSITION_INDIVIDUAL_ACCOUNT_WITH_ORG, ONBOARDING_START_PAGE_ADD_DATA
from ckanext.hdx_users.tests.test_onboarding_v2.helper import _apply_for_user_account, _validate_account, _attempt_login
from ckan.tests.helpers import CKANTestApp

came_from_list = [
    {
        'came_from': {
            'start_page': {
                'page_type': ONBOARDING_START_PAGE_HDX_CONNECT,
                'additional_params': {'dataset_id': 'some-dataset-id'}
            },
            'value_proposition_page': ONBOARDING_VALUE_PROPOSITION_INDIVIDUAL_ACCOUNT
        },
        'redirect_to': {
            'flask_view': 'hdx_dataset.read',
            'other_params': {
                'id': 'some-dataset-id'
            }
        }
    },
    {
        'came_from': {
            'start_page': {
                'page_type': ONBOARDING_START_PAGE_CONTACT_CONTRIBUTOR,
                'additional_params': {'dataset_id': 'some-dataset-id'}
            },
            'value_proposition_page': ONBOARDING_VALUE_PROPOSITION_INDIVIDUAL_ACCOUNT
        },
        'redirect_to': {
            'flask_view': 'hdx_dataset.read',
            'other_params': {
                'id': 'some-dataset-id'
            }
        }
    },
    {
        'came_from': {
            'start_page': {
                'page_type': ONBOARDING_START_PAGE_ADD_DATA,
            },
            'value_proposition_page': ONBOARDING_VALUE_PROPOSITION_INDIVIDUAL_ACCOUNT
        },
        'redirect_to': {
            'flask_view': 'dashboard.organizations',
            'other_params': {}
        }
    },
    {
        'came_from': {
            'start_page': {
                'page_type': ONBOARDING_START_PAGE_HDX_CONNECT,
                'additional_params': {'dataset_id': 'some-dataset-id'}
            },
            'value_proposition_page': ONBOARDING_VALUE_PROPOSITION_INDIVIDUAL_ACCOUNT_WITH_ORG
        },
        'redirect_to': {
            'flask_view': 'hdx_org_join.org_join',
            'other_params': {}
        }
    },
]

@pytest.mark.usefixtures('clean_db', 'clean_index', 'with_request_context')
@pytest.mark.ckan_config('ckanext.security.brute_force_key', 'user_name')
@pytest.mark.parametrize('came_from_entry', came_from_list)
@mock.patch('ckanext.hdx_users.logic.first_login.FirstLoginAnalyticsSender.send_to_queue')
@mock.patch('ckanext.security.authenticator.LoginThrottle')
@mock.patch('ckanext.hdx_users.helpers.tokens.send_validation_email')
def test_came_from_logic(mock_send_validation_email: MagicMock, MockLoginThrottle: MagicMock,
                         mock_analytics_send_to_queue: MagicMock,
                         app: CKANTestApp, came_from_entry: Dict):
    '''
    Check the documentation of the `test_user_login()` function
    '''
    MockLoginThrottle.return_value.is_locked.return_value = False
    came_from = came_from_entry['came_from']
    redirect_to = came_from_entry['redirect_to']
    redirect_to_url = tk.url_for(redirect_to['flask_view'], **redirect_to['other_params'])

    _apply_for_user_account(app, {'came_from': json.dumps(came_from)})
    token = mock_send_validation_email.call_args[0][1]['token']
    _validate_account(app, token)
    login_response = _attempt_login(app, follow_redirects=False)
    assert login_response.status_code == 302
    assert redirect_to_url in login_response.location
    assert mock_analytics_send_to_queue.call_count == 1
