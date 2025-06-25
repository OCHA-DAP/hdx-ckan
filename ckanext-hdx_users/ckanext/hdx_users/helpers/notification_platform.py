import logging
from ckan.common import current_user
from typing import Any, Dict, Optional, Tuple

from ckan.plugins import toolkit as tk
from ckanext.hdx_users.controller_logic.notification_platform_logic import verify_unsubscribe_token
from ckanext.hdx_users.general_token_model import ObjectType, get_by_type_and_user_id_and_object, TokenType

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
    unsubscribe_token_validated = False
    if unsubscribe_token:
        try:
            unsubscribe_token = verify_unsubscribe_token(unsubscribe_token, inactivate=False)
            unsubscribe_token_validated = True
        except Exception as e:
            unsubscribe_token = None
            h.flash_error('Your token is invalid or has expired.')
    else:
        unsubscribe_token = get_by_type_and_user_id_and_object(TokenType.UNSUBSCRIBE_FOR_NOTIFICATION, current_user.email, object_type, object_id)


    template_data['unsubscribe_token'] = unsubscribe_token
    template_data['unsubscribe_token_validated'] = unsubscribe_token_validated
