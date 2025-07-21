import logging
import requests

import ckan.plugins.toolkit as tk

from ckanext.hdx_theme.helpers.helpers import hdx_supports_notifications
from ckanext.hdx_users.general_token_model import ObjectType, HDXGeneralToken
from ckanext.hdx_users.helpers.notification_platform import read_novu_config


log = logging.getLogger(__name__)


def add_subscription_info(
    email: str,
    object_type: ObjectType,
    object_id: str,
    unsubscribe_token_obj: HDXGeneralToken,
):


    novu_api_key, novu_api_url = read_novu_config()
    unsubscribe_token_key = _generate_unsubscribe_token_key(object_id, object_type)

    if not email or not object_id:
        raise tk.ValidationError('Missing required parameters: email and object_id')

    notifications_enabled = hdx_supports_notifications(object_type, object_id)
    if not notifications_enabled:
        raise tk.ValidationError('Notifications are not enabled for the dataset')

    headers = {
        'Authorization': f'ApiKey {novu_api_key}',
        'Content-Type': 'application/json'
    }

    # Use the email as the subscriber ID
    subscriber_id = email

    response = requests.get(f'{novu_api_url}/subscribers/{subscriber_id}', headers=headers)

    if response.status_code == 404:
        # Subscriber doesn't exist; create a new one
        subscriber_data = {
            'subscriberId': subscriber_id,
            'email': email,
            'data': {
                unsubscribe_token_key: unsubscribe_token_obj.token,
            }
        }
        response = requests.post(f'{novu_api_url}/subscribers', json=subscriber_data, headers=headers)
        if response.status_code != 201:
            raise Exception(f'Failed to create subscriber: {response.text}')

    elif response.status_code == 200:
        data = response.json().get('data', {}).get('data', {})
        data[unsubscribe_token_key] = unsubscribe_token_obj.token
        subscriber_data = {
            'data': data
        }
        response = requests.put(f'{novu_api_url}/subscribers/{email}', json=subscriber_data, headers=headers)
        if response.status_code != 200:
            raise Exception(f'Failed to update subscriber: {response.text}')
    else:
        raise Exception(f'Error checking subscriber: {response.text}')

    if response.status_code != 200:
        raise Exception(f'Failed to add subscriber to topic: {response.text}')

    return {'message': f'You have successfully subscribed to notifications for this dataset.'}


def remove_subscription_info(email: str, object_id: str, object_type: ObjectType):
    novu_api_key, novu_api_url = read_novu_config()
    headers = {
        'Authorization': f'ApiKey {novu_api_key}',
        'Content-Type': 'application/json'
    }

    # Use the email as the subscriber ID
    subscriber_id = email
    unsubscribe_token_key = _generate_unsubscribe_token_key(object_id, object_type)

    response = requests.get(f'{novu_api_url}/subscribers/{subscriber_id}', headers=headers)

    # If the subscriber exists, remove the unsubscribe token from its data. If the data is empty, remove the subscriber
    if response.status_code == 200:
        data = response.json().get('data', {}).get('data', {})
        if unsubscribe_token_key in data:
            del data[unsubscribe_token_key]
            if data:
                subscriber_data = {
                    'data': data
                }
                response = requests.put(f'{novu_api_url}/subscribers/{email}', json=subscriber_data, headers=headers)
                if response.status_code != 200:
                    log.error(f'Failed to update subscriber: {response.text}')
                    raise Exception(f'Failed to update subscriber: {response.text}')
            else:
                # If the data is empty, remove the subscriber
                response = requests.delete(f'{novu_api_url}/subscribers/{email}', headers=headers)
                if response.status_code != 204:
                    raise Exception(f'Failed to delete subscriber: {response.text}')
        else:
            log.warning(f'Unsubscribe token key {unsubscribe_token_key} not found in subscriber data')

    elif response.status_code == 404:
        log.warning(f'Subscriber {subscriber_id} not found')
    else:
        raise Exception(f'Error checking subscriber: {response.text}')


def _generate_unsubscribe_token_key(object_id: str, object_type: ObjectType) -> str:
    if object_type == ObjectType.DATASET:
        type = ''  # this is the default, for historical reasons
    else:
        type = object_type.value + '_'
    unsubscribe_token_key = 'unsubscribe_token_' + type + object_id.replace('-', '_')
    return unsubscribe_token_key

