import logging

from hashlib import md5
from typing import Optional

from ckan.common import current_user
from ckan.types import Context, Request
from ckanext.hdx_theme.util.analytics import AbstractAnalyticsSender
from ckanext.hdx_users.general_token_model import ObjectType

import ckan.plugins.toolkit as tk

log = logging.getLogger(__name__)

get_action = tk.get_action


class FirstLoginAnalyticsSender(AbstractAnalyticsSender):

    @classmethod
    def _get_action_name(cls) -> str:
        return 'first login'

    @classmethod
    def _replace_special_chars_with_space(cls, input_str: str) -> str:
        if input_str:
            return input_str.replace('_', ' ').replace('-', ' ')

    def __init__(self, onboarding_start: str, account_choice: str):
        super().__init__()
        cleaned_onboarding_start = self._replace_special_chars_with_space(onboarding_start)
        cleaned_account_choice = self._replace_special_chars_with_space(account_choice)

        self.analytics_dict = {
            'event_name': self._get_action_name(),
            'mixpanel_meta': {
                'onboarding start': cleaned_onboarding_start,
                'account choice': cleaned_account_choice
            },
            'ga_meta': {
                'ec': 'organization',  # event category
                'ea': self._get_action_name(),  # event action
                'el': cleaned_account_choice,  # event label
                'cd1': cleaned_onboarding_start
            }
        }


class EmailValidationAnalyticsSender(AbstractAnalyticsSender):

    @classmethod
    def _get_object_name(cls, object_type: Optional[ObjectType] = None, object_id: Optional[str] = None) -> Optional[str]:
        object_name = None

        if object_type and object_id:
            action = None
            if object_type == ObjectType.DATASET:
                action = 'package_show'
            elif object_type == ObjectType.GROUP:
                action = 'group_show'
            elif object_type == ObjectType.ORGANIZATION:
                action = 'organization_show'
            elif object_type == ObjectType.CRISIS:
                action = 'page_show'
            else:
                log.error(f'Invalid object_type: {object_type} in email validation analytics')

            try:
                object_obj = get_action(action)({}, {'id': object_id})
                object_name = object_obj.get('name')
            except tk.ObjectNotFound:
                log.error(f'{object_type} {object_id} does not exist in email validation analytics')
            except Exception as e:
                log.error(f'Error retrieving object or user: {e} in email validation analytics')

        return object_name

    def __init__(self, validation_type: str, validation_status: bool, email: str,
                 object_type: Optional[ObjectType] = None, object_id: Optional[str] = None):
        super(EmailValidationAnalyticsSender, self).__init__()
        event_name = 'email validation'

        email = email.strip().lower() if email else ''
        email_hash = md5(email.encode('utf8')).hexdigest() if email else ''
        object_name = self._get_object_name(object_type, object_id)
        authenticated = current_user.is_authenticated

        self.analytics_dict = {
            'event_name': event_name,
            'mixpanel_meta': {
                'type': validation_type,
                'successful': validation_status,
                'email hash': email_hash,
                'object id': object_id,
                'object name': object_name,
                'object type': object_type,
                'authenticated': authenticated,
            },
            'ga_meta': {}
        }


class APITokenCreationAnalyticsSender(AbstractAnalyticsSender):

    @classmethod
    def _get_user_email_from_username(cls, username: str) -> Optional[str]:
        try:
            context: Context = {'keep_email': True, 'ignore_auth': True}
            user_dict = tk.get_action('user_show')(context, {'id': username})
            return user_dict.get('email', '').strip().lower()
        except Exception as e:
            log.error(f"Error retrieving email for user {username}: {e}")
            return None

    @classmethod
    def _get_api_creation_source(cls, username: str, request: Request) -> Optional[str]:
        if not request:
            return None

        request_path = request.path.strip('/')
        if not request_path:
            return None

        api_paths = {'api/action/api_token_create', 'api/3/action/api_token_create'}
        ui_paths = {f'user/{username}/api-tokens'}

        if request_path in api_paths:
            return 'api'
        elif request_path in ui_paths:
            return 'ui'

        return None

    def __init__(self, token_name: str, username: str, request: Request = None):
        super(APITokenCreationAnalyticsSender, self).__init__()
        event_name = 'api token creation'

        source = self._get_api_creation_source(username, request)
        email = self._get_user_email_from_username(username)
        email_hash = md5(email.encode('utf8')).hexdigest() if email else ''

        self.analytics_dict = {
            'event_name': event_name,
            'mixpanel_meta': {
                'token name': token_name,
                'source': source,
                'email hash': email_hash,
            },
            'ga_meta': {}
        }
