import logging
from typing import Tuple

from ckan.plugins import toolkit as tk
from ckanext.hdx_package.helpers.caching import cached_datasets_with_notifications

log = logging.getLogger(__name__)

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

