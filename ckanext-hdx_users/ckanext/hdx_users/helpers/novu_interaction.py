import logging
import requests
from typing import Optional, Dict, Any

import ckan.plugins.toolkit as tk

from ckanext.hdx_theme.helpers.helpers import hdx_supports_notifications
from ckanext.hdx_users.general_token_model import ObjectType, HDXGeneralToken
from ckanext.hdx_users.helpers.notification_platform import read_novu_config


log = logging.getLogger(__name__)


class NovuDAO:
    """Data Access Object for Novu API interactions"""

    def __init__(self) -> None:
        self.novu_api_key, self.novu_api_url = read_novu_config()
        self.headers = {
            'Authorization': f'ApiKey {self.novu_api_key}',
            'Content-Type': 'application/json'
        }

    def get_subscriber(self, subscriber_id: str) -> Optional[Dict[str, Any]]:
        """Get subscriber information from Novu API

        :param subscriber_id: The ID of the subscriber to retrieve
        :type subscriber_id: str
        :returns: Subscriber data if found, None if subscriber doesn't exist
        :rtype: Optional[Dict[str, Any]]
        :raises Exception: If there's an error checking subscriber
        """
        response = requests.get(f'{self.novu_api_url}/subscribers/{subscriber_id}', headers=self.headers)

        if response.status_code == 404:
            return None
        elif response.status_code == 200:
            return response.json().get('data', {})
        else:
            raise Exception(f'Error checking subscriber: {response.text}')

    def create_subscriber(self, subscriber_data: Dict[str, Any]) -> None:
        """Create a new subscriber in Novu API

        :param subscriber_data: Dictionary containing subscriber information
        :type subscriber_data: Dict[str, Any]
        :raises Exception: If subscriber creation fails
        """
        response = requests.post(f'{self.novu_api_url}/subscribers', json=subscriber_data, headers=self.headers)
        if response.status_code != 201:
            raise Exception(f'Failed to create subscriber: {response.text}')

    def update_subscriber(self, subscriber_id: str, subscriber_data: Dict[str, Any]) -> None:
        """Update an existing subscriber in Novu API

        :param subscriber_id: ID of the subscriber to update
        :type subscriber_id: str
        :param subscriber_data: Dictionary containing updated subscriber information
        :type subscriber_data: Dict[str, Any]
        :raises Exception: If subscriber update fails
        """
        response = requests.put(f'{self.novu_api_url}/subscribers/{subscriber_id}', json=subscriber_data, headers=self.headers)
        if response.status_code != 200:
            raise Exception(f'Failed to update subscriber: {response.text}')

    def delete_subscriber(self, subscriber_id: str) -> None:
        """Delete a subscriber from Novu API

        :param subscriber_id: ID of the subscriber to delete
        :type subscriber_id: str
        :raises Exception: If subscriber deletion fails
        """
        response = requests.delete(f'{self.novu_api_url}/subscribers/{subscriber_id}', headers=self.headers)
        if response.status_code not in [200, 204]:
            raise Exception(f'Failed to delete subscriber: {response.text}')

    def subscriber_exists(self, subscriber_id: str) -> bool:
        """Check if a subscriber exists

        :param subscriber_id: ID of the subscriber to check
        :type subscriber_id: str
        :returns: True if subscriber exists, False otherwise
        :rtype: bool
        """
        try:
            return self.get_subscriber(subscriber_id) is not None
        except Exception:
            return False


def add_subscription_info(
    subscriber_id: str,
    email: str,
    unsubscribe_token_obj: HDXGeneralToken,
    object_type: ObjectType,
    object_id: str,
    object_dict: Optional[dict[str, Any]] = None,
):
    novu_dao = NovuDAO()
    unsubscribe_token_key = _generate_unsubscribe_token_key(object_id, object_type)

    if not subscriber_id or not email or not object_id:
        raise tk.ValidationError('Missing required parameters: subscriber_id, email or object_id')

    notifications_enabled = hdx_supports_notifications(object_type, object_id, object_dict)
    if not notifications_enabled:
        raise tk.ValidationError(f'Notifications are not enabled for the {object_type.display_name}')

    subscriber_data = novu_dao.get_subscriber(subscriber_id)

    if subscriber_data is None:
        # Subscriber doesn't exist; create a new one
        new_subscriber_data = {
            'subscriberId': subscriber_id,
            'email': email,
            'data': {
                unsubscribe_token_key: unsubscribe_token_obj.token,
            }
        }
        novu_dao.create_subscriber(new_subscriber_data)
    else:
        # Subscriber exists, update their data
        existing_data = subscriber_data.get('data', {})
        existing_data[unsubscribe_token_key] = unsubscribe_token_obj.token
        update_data = {
            'data': existing_data
        }
        novu_dao.update_subscriber(subscriber_id, update_data)

    return {'message': f'You have successfully subscribed to notifications for this dataset.'}


def remove_subscription_info(subscriber_id: str, object_id: str, object_type: ObjectType):
    novu_dao = NovuDAO()

    unsubscribe_token_key = _generate_unsubscribe_token_key(object_id, object_type)

    subscriber_data = novu_dao.get_subscriber(subscriber_id)

    if subscriber_data is None:
        log.warning(f'Subscriber {subscriber_id} not found')
        return

    # If the subscriber exists, remove the unsubscribe token from its data
    existing_data = subscriber_data.get('data', {})
    if unsubscribe_token_key in existing_data:
        del existing_data[unsubscribe_token_key]
        if existing_data:
            # Update subscriber with remaining data
            update_data = {
                'data': existing_data
            }
            novu_dao.update_subscriber(subscriber_id, update_data)
        else:
            # If no data remains, remove the subscriber entirely
            novu_dao.delete_subscriber(subscriber_id)
    else:
        log.warning(f'Unsubscribe token key {unsubscribe_token_key} not found in subscriber data')


def _generate_unsubscribe_token_key(object_id: str, object_type: ObjectType) -> str:
    if object_type == ObjectType.DATASET:
        type = ''  # this is the default, for historical reasons
    else:
        type = object_type.value + '_'
    unsubscribe_token_key = 'unsubscribe_token_' + type + object_id.replace('-', '_')
    return unsubscribe_token_key
