import logging
import ckan.plugins.toolkit as tk

from flask import Blueprint
from ckan.types import Response

_h = tk.h

log = logging.getLogger(__name__)

hdx_notifications = Blueprint(u'hdx_notifications', __name__, url_prefix=u'/notifications')


def _verify_token(email:str, token: str) -> bool:
    return True


def subscribe_to_dataset() -> Response:
    # Get parameters from the URL
    email = tk.request.args.get('email')
    dataset_id = tk.request.args.get('dataset_id')
    token = tk.request.args.get('token')

    dataset_list_url = tk.url_for('dataset.search')
    token_valid = _verify_token(email, token)
    if not token_valid:
        _h.flash_error('Your token is invalid or has expired. Please try to subscribe again.')
        return tk.redirect_to(dataset_list_url)

    if not email or not dataset_id:
        _h.flash_error('Missing required parameters: email and dataset_id.')
        return tk.redirect_to(dataset_list_url)

    context = {'ignore_auth': True}
    data_dict = {'email': email, 'dataset_id': dataset_id}

    try:
        result = tk.get_action('hdx_add_notification_subscription')(context, data_dict)
        _h.flash_success(result['message'])
    except tk.ValidationError as e:
        log.error('An exception occurred:' + str(e))
        _h.flash_error(str(e))
    except Exception as e:
        log.error('An exception occurred:' + str(e))
        _h.flash_error('An error occurred: ' + str(e))

    # Redirect to the dataset page
    dataset_url = tk.url_for('dataset.read', id=dataset_id)
    return tk.redirect_to(dataset_url)


def unsubscribe_from_dataset() -> Response:
    # Get parameters from the URL
    email = tk.request.args.get('email')
    dataset_id = tk.request.args.get('dataset_id')
    token = tk.request.args.get('token')

    dataset_list_url = tk.url_for('dataset.search')
    token_valid = _verify_token(email, token)
    if not token_valid:
        _h.flash_error('Your token is invalid.')
        return tk.redirect_to(dataset_list_url)

    if not email or not dataset_id:
        _h.flash_error('Missing required parameters: email and dataset_id.')
        return tk.redirect_to(dataset_list_url)

    context = {'ignore_auth': True}
    data_dict = {'email': email, 'dataset_id': dataset_id}

    try:
        result = tk.get_action('hdx_delete_notification_subscription')(context, data_dict)
        _h.flash_success(result['message'])
    except tk.ValidationError as e:
        log.error('An exception occurred:' + str(e))
        _h.flash_error(str(e))
    except Exception as e:
        log.error('An exception occurred:' + str(e))
        _h.flash_error('An error occurred: ' + str(e))

    # Redirect to the dataset page
    dataset_url = tk.url_for('dataset.read', id=dataset_id)
    return tk.redirect_to(dataset_url)

hdx_notifications.add_url_rule(u'/subscribe-to-dataset', view_func=subscribe_to_dataset)
hdx_notifications.add_url_rule(u'/unsubscribe-from-dataset', view_func=unsubscribe_from_dataset)
