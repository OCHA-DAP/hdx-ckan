import logging
from ckan.types import Request
from typing import Any, Dict, Tuple

from ckan.plugins import toolkit as tk
from ckanext.hdx_package.helpers.caching import cached_datasets_with_notifications
from ckanext.hdx_users.controller_logic.notification_platform_logic import verify_unsubscribe_token

log = logging.getLogger(__name__)

h = tk.h

def check_notifications_enabled_for_dataset(dataset_id: str) -> bool:
    datasets = cached_datasets_with_notifications()
    return dataset_id in datasets


def read_novu_config() -> Tuple[str, str]:
    # Novu API configuration
    novu_api_url = tk.config.get('hdx.notifications.novu.api_url')
    novu_api_key = tk.config.get('hdx.notifications.novu.api_key')
    if not novu_api_key:
        log.warning('Novu api key is missing. Skipping subscription action.')
        raise Exception(f'Notification subscriptions are not enabled on HDX')
    return novu_api_key, novu_api_url


def add_unsubscribe_token(request: Request, template_data: Dict[str, Any]) -> None:
    unsubscribe_token = request.args.get('_unsubscribe_token', None)
    if unsubscribe_token:
        try:
            unsubscribe_token = verify_unsubscribe_token(unsubscribe_token, inactivate=False)
        except Exception as e:
            unsubscribe_token = None
            h.flash_error('Your token is invalid or has expired.')

    template_data['unsubscribe_token'] = unsubscribe_token
