import json
import requests
import logging

import ckan.plugins.toolkit as tk
import ckanext.hdx_theme.helpers.helpers as theme_h

from ckan.types import DataDict, Context
from ckanext.hdx_users.helpers.notification_platform import read_novu_config

_get_or_bust = tk.get_or_bust
ValidationError = tk.ValidationError
_check_access = tk.check_access
NotFound = tk.ObjectNotFound
NotAuthorized = tk.NotAuthorized
get_action = tk.get_action
chained_action = tk.chained_action
OnbUserNotFound = json.dumps({'success': False, 'error': {'message': 'User not found'}})
OnbSuccess = json.dumps({'success': True})


log = logging.getLogger(__name__)


@chained_action
def hdx_user_delete(original_action, context, data_dict):
    '''Delete a user. If user is maintainer for a datasets, it returns error
    copied&adapted from ckan/logic/action/delete.py:L36

    Only sysadmins can delete users.

    :param id: the id or username of the user to delete
    :type id: string
    '''

    _check_access('user_delete', context, data_dict)

    model = context['model']
    user_username = _get_or_bust(data_dict, 'id')
    user_obj = model.User.get(user_username)
    if user_obj:
        user_id = user_obj.id
        if user_id:
            org_list = get_action('organization_list_for_user')(context, {'id': user_id})
            if org_list:
                for org in org_list:
                    pkg_list_for_maintainer = theme_h._get_packages_for_maintainer(context, user_id, org.get('name'))
                    if pkg_list_for_maintainer and len(pkg_list_for_maintainer) > 0:
                        raise NotAuthorized('User can not be deleted as it is maintainer for datasets')

    return original_action(context, data_dict)

def hdx_delete_notification_subscription(context: Context, data_dict: DataDict):
    tk.check_access('hdx_delete_notification_subscription', context, {})

    novu_api_key, novu_api_url = read_novu_config()

    email = data_dict.get('email')
    dataset_id = data_dict.get('dataset_id')

    if not email or not dataset_id:
        raise tk.ValidationError('Missing required parameters: email and dataset_id')


    headers = {
        'Authorization': f'ApiKey {novu_api_key}',
        'Content-Type': 'application/json'
    }

    # Use the email as the subscriber ID
    subscriber_id = email

    topic_key = f'dataset-{dataset_id}'

    # Check if the topic exists
    response = requests.get(f'{novu_api_url}/topics/{topic_key}', headers=headers)
    if response.status_code == 200:
        topic_subscribers = response.json().get('data', {}).get('subscribers', [])
        remove_subscriber_data = {
            'subscribers': [subscriber_id]
        }
        subscriber_removal_response = requests.post(f'{novu_api_url}/topics/{topic_key}/subscribers/removal',
                                                    json=remove_subscriber_data, headers=headers)

        if subscriber_removal_response.status_code not in (200, 204):
            raise Exception(
                f'Failed to remove subscriber {subscriber_id} from dataset: {subscriber_removal_response.text}')
        elif len(topic_subscribers) == 1 and topic_subscribers[0] == subscriber_id:
            topic_removal_response = requests.delete(f'{novu_api_url}/topics/{topic_key}', headers=headers)
            if topic_removal_response.status_code not in (200, 204):
                raise Exception(f'Failed to remove topic {topic_key} from dataset: {subscriber_removal_response.text}')

    else:
        if response.status_code == 404:
            log.error(f'Topic was not found in Novu')
        log.error(
            f'Got status code {response.status_code} when checking if the database exists. Response: {response.text}')
        raise Exception(f'Failed to remove subscriber from dataset')

    return {'message': f' {email}  unsubscribed from further notifications.'}
