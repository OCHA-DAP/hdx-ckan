import json
import logging
from enum import Enum

from typing import Union
from typing_extensions import TypedDict

import ckan.plugins.toolkit as tk
from ckan.types import Context

from ckanext.hdx_users.helpers.constants import (
    ONBOARDING_VALUE_PROPOSITION_INDIVIDUAL_ACCOUNT_WITH_ORG,
    ONBOARDING_VALUE_PROPOSITION_INDIVIDUAL_ACCOUNT,
    ONBOARDING_START_PAGE_HDX_CONNECT,
    ONBOARDING_START_PAGE_CONTACT_CONTRIBUTOR,
    ONBOARDING_START_PAGE_ADD_DATA,
    ONBOARDING_CAME_FROM_EXTRAS_KEY,
    ONBOARDING_CAME_FROM_STATE_EXTRAS_KEY,
)

get_action = tk.get_action
check_access = tk.check_access
g = tk.g


log = logging.getLogger(__name__)

class FirstLoginLogic:
    def __init__(self, context: Context, user_id: str):
        self.context = context
        self.user_id = user_id
        self.state = None

    def determine_initial_redirect_and_mark_first_login(self) -> Union[str, None]:
        '''
        Determine where the user should be redirected to at first login
        '''
        onboarding_source_str = self._get_onboarding_came_from()
        try:
            onboarding_source: 'OnboardingSource' = json.loads(onboarding_source_str)
            url = self._compute_url(onboarding_source)
            return url
        except Exception as e:
            log.error(str(e))

        return None

    def _compute_url(self, onboarding_source: 'OnboardingSource') -> Union[str, None]:
        '''
        Compute the route to redirect the user to based on the onboarding source
        '''
        if onboarding_source['value_proposition_page'] == ONBOARDING_VALUE_PROPOSITION_INDIVIDUAL_ACCOUNT:
            start_page = onboarding_source['start_page']
            if start_page['page_type'] in [ONBOARDING_START_PAGE_HDX_CONNECT, ONBOARDING_START_PAGE_CONTACT_CONTRIBUTOR]:
                dataset_id = start_page['additional_params']['dataset_id']
                return tk.url_for('hdx_dataset.read', id=dataset_id)
            elif start_page['page_type'] == ONBOARDING_START_PAGE_ADD_DATA:
                return tk.url_for('dashboard.organization')
        elif onboarding_source['value_proposition_page'] == ONBOARDING_VALUE_PROPOSITION_INDIVIDUAL_ACCOUNT_WITH_ORG:
            return tk.url_for('dashboard.organizations')
        return None

    def _get_onboarding_came_from(self) -> Union[str, None]:
        check_access('user_extra_show', self.context, {'user_id': self.user_id})

        ue_user = get_action('user_extra_value_by_keys_show')(
            self.context,
            {
                'user_id': self.user_id,
                'keys': [ONBOARDING_CAME_FROM_EXTRAS_KEY, ONBOARDING_CAME_FROM_STATE_EXTRAS_KEY]
            }
        )
        came_from, state = self._get_user_extra(ue_user)
        self.state = state
        if state == 'inactive':
            return None
        if state == 'active' and came_from:
            return came_from
        return None


    def _get_user_extra(self, ue_user):
        state = 'inactive'
        came_from = None
        for ue_item in ue_user:
            if ue_item.get('key') == ONBOARDING_CAME_FROM_STATE_EXTRAS_KEY:
                state = ue_item.get('value')
            if ue_item.get('key') == ONBOARDING_CAME_FROM_EXTRAS_KEY:
                came_from = ue_item.get('value')
        return came_from, state

    def mark_state_as_used_if_needed(self) -> bool:
        '''
        Mark in the database that the user had the first login and was redirected to the page he initially desired.
        '''
        if self.state == 'active':
            data_dict = {
                'user_id': self.user_id,
                'extras': [
                    {
                        'key': ONBOARDING_CAME_FROM_STATE_EXTRAS_KEY,
                        'new_value': 'inactive'
                    }
                ]
            }
            result = get_action('user_extra_update')(self.context, data_dict)
            if (len(result) == 1
                and result[0]['key'] == ONBOARDING_CAME_FROM_STATE_EXTRAS_KEY and result[0]['value'] == 'inactive'):
                self.state = 'inactive'
                log.info('User {} logged in for the first time'.format(self.user_id))
                return True
            else:
                log.error('Something went wrong while trying to mark "came from" state as inactive'
                          ' after first login for user {}'.format(self.user_id))
            return False


class OnboardingSource(TypedDict, total=False):
    start_page: 'StartPage'
    value_proposition_page: str

class StartPage(TypedDict, total=False):
    page_type: 'PageTypeValues'
    additional_params: 'AdditionalParams'

class PageTypeValues(str, Enum):
    hdx_connect = ONBOARDING_START_PAGE_HDX_CONNECT
    contact_contributor = ONBOARDING_START_PAGE_CONTACT_CONTRIBUTOR
    add_data = ONBOARDING_START_PAGE_ADD_DATA

class AdditionalParams(TypedDict, total=False):
    dataset_id: str

class ValuePropositionValues(str, Enum):
    individual_account = ONBOARDING_VALUE_PROPOSITION_INDIVIDUAL_ACCOUNT
    individual_account_with_org = ONBOARDING_VALUE_PROPOSITION_INDIVIDUAL_ACCOUNT_WITH_ORG
