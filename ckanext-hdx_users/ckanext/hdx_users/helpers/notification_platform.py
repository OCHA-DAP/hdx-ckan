import logging
from ckan.common import current_user
from typing import Any, Dict, Optional, Tuple

from ckan.plugins import toolkit as tk
from ckan.types import Context
from ckanext.hdx_users.controller_logic.notification_platform_logic import get_unsubscribe_token
from ckanext.hdx_users.general_token_model import ObjectType, get_by_type_and_user_id_and_object, TokenType, \
    HDXGeneralToken

log = logging.getLogger(__name__)

h = tk.h


def read_novu_config() -> Tuple[str, str]:
    # Novu API configuration
    novu_api_url = tk.config.get('hdx.notifications.novu.api_url')
    novu_api_key = tk.config.get('hdx.notifications.novu.api_key')
    if not novu_api_key:
        log.warning('Novu api key is missing. Skipping subscription action.')
        raise Exception(f'Notification subscriptions are not enabled on HDX')
    return novu_api_key, novu_api_url


def add_unsubscribe_token(unsubscribe_token: Optional[str], object_type: ObjectType, object_id: str,
                          template_data: Dict[str, Any]) -> None:
    """
    Adds the unsubscribe token to the template data so that it can be used in the page
    """
    unsubscribe_token_validated = False
    unsubscribe_email = ''
    unsubscribe_token_invalidate = False

    if unsubscribe_token:
        try:
            unsubscribe_token = get_unsubscribe_token(unsubscribe_token)
            unsubscribe_token_validated = True
            unsubscribe_email = _get_user_email_from_unsubscribe_token(unsubscribe_token)
        except Exception as e:
            unsubscribe_token = None
            unsubscribe_token_invalidate = True
            h.flash_error('Your token is invalid or has expired.')
    elif current_user.is_authenticated:
        unsubscribe_token = get_by_type_and_user_id_and_object(TokenType.UNSUBSCRIBE_FOR_NOTIFICATION, current_user.id, object_type, object_id)
        unsubscribe_email = current_user.email
        unsubscribe_token_invalidate = True

    template_data['unsubscribe_token'] = unsubscribe_token
    template_data['unsubscribe_email'] = unsubscribe_email
    template_data['unsubscribe_token_validated'] = unsubscribe_token_validated
    template_data['unsubscribe_token_invalidate'] = unsubscribe_token_invalidate


def _get_user_email_from_unsubscribe_token(unsubscribe_token: HDXGeneralToken) -> str:
    context: Context = {
        'keep_email': True,
        'ignore_auth': True
    }
    user_dict = tk.get_action('user_show')(context, {'id': unsubscribe_token.user_id})

    return user_dict.get('email', '')
