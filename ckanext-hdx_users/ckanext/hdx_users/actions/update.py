import logging
import requests
import ckan.plugins.toolkit as tk
import ckanext.hdx_users.helpers.mailer as hdx_mailer
import ckanext.hdx_users.helpers.reset_password as reset_password
import ckanext.hdx_users.model as umodel
from ckan.types import Context, DataDict
from ckanext.hdx_users.helpers.notification_platform import check_notifications_enabled_for_dataset, read_novu_config
from ckanext.hdx_users.helpers.token_expiration_helper import find_expiring_api_tokens, send_emails_for_expiring_tokens
from ckanext.hdx_users.logic.schema import onboarding_default_update_user_schema


NotFound = tk.ObjectNotFound
_check_access = tk.check_access
_get_or_bust = tk.get_or_bust
ValidationError = tk.ValidationError
get_action = tk.get_action
config = tk.config

log = logging.getLogger(__name__)

def token_update(context, data_dict):
    token = data_dict.get('token')
    token_obj = umodel.ValidationToken.get_by_token(token=token)
    if token_obj is None:
        raise NotFound
    # Logged in user should have edit access to account token belongs to
    _check_access('user_update', context, {'id': token_obj.user_id})
    session = context["session"]
    token_obj.valid = True
    session.add(token_obj)
    session.commit()
    return token_obj.as_dict()


def hdx_send_reset_link(context, data_dict):
    from six.moves.urllib.parse import urljoin

    import ckan.lib.helpers as h

    model = context['model']

    user = None
    reset_link = None
    user_fullname = None
    recipient_mail = None

    id = data_dict.get('id', None)
    if id:
        user = model.User.get(id)
        context['user_obj'] = user
        if user is None:
            raise NotFound

    expiration_in_minutes = config.get('hdx.password.reset_key.expiration_in_minutes')
    if user:
        reset_password.create_reset_key(user, expiration_in_minutes)

        recipient_mail = user.email if user.email else None
        user_fullname = user.fullname or ''
        reset_link = urljoin(config.get('ckan.site_url'),
                             h.url_for(controller='user', action='perform_reset', id=user.id, key=user.reset_key))

    email_data = {
        'user_fullname': user_fullname,
        'user_reset_link': reset_link,
        'expiration_in_minutes': expiration_in_minutes,
    }
    if recipient_mail:
        subject = u'HDX password reset'
        hdx_mailer.mail_recipient([{'display_name': user_fullname, 'email': recipient_mail}], subject,
                                  email_data, footer=recipient_mail,
                                  snippet='email/content/password_reset.html')


def notify_users_about_api_token_expiration(context, data_dict):
    '''
    :param days_in_advance: how many days in advance we should look for expiring api tokens
    :type days_in_advance: int
    :param expires_on_specified_day: if True then we're looking only for api tokens that will expire on the
        specified day. Otherwise, we look for tokens that expire from now till the specified day.
    :type expires_on_specified_day: bool
    :return: number of api tokens that will expire
    '''
    _check_access('notify_users_about_api_token_expiration', context, {})
    days_in_advance, expires_on_specified_day = __extract_token_expiration_params(data_dict)

    model = context['model']
    session = context['model'].Session

    token_info_list, period_start_string, period_end_string = \
        find_expiring_api_tokens(model, session, days_in_advance, expires_on_specified_day)
    number_of_emails = send_emails_for_expiring_tokens(token_info_list)
    return {
        'start_date': period_start_string,
        'end_date': period_end_string,
        'emails_sent': number_of_emails,
    }


def __extract_token_expiration_params(data_dict):
    days_in_advance = _get_or_bust(data_dict, 'days_in_advance')
    try:
        days_in_advance = int(days_in_advance)
        expires_on_specified_day = data_dict.get('expires_on_specified_day') == 'true' \
                                   or data_dict.get('expires_on_specified_day') is True
    except ValueError:
        raise ValidationError('Limit must be a positive integer')
    return days_in_advance, expires_on_specified_day


@tk.chained_action
def user_update(up_func, context, data_dict):
    """
    Perform user_update with a modified default schema.

    This function overrides the default schema used for updating users with a modified schema. By default,
    it uses the schema specified by the 'onboarding_default_update_user_schema' function. If a schema is already
    provided in the context, it will use that instead.
    """
    context['schema'] = context.get('schema') or onboarding_default_update_user_schema()

    result = up_func(context, data_dict)
    return result


def hdx_add_notification_subscription(context: Context, data_dict: DataDict):
    tk.check_access('hdx_add_notification_subscription', context, {})

    novu_api_key, novu_api_url = read_novu_config()

    email = data_dict.get('email')
    dataset_id = data_dict.get('dataset_id')
    unsubscribe_token = data_dict.get('unsubscribe_token')
    unsubscribe_token_key = 'unsubscribe_token_' + dataset_id.replace('-', '_')

    if not email or not dataset_id:
        raise tk.ValidationError('Missing required parameters: email and dataset_id')

    notifications_enabled = check_notifications_enabled_for_dataset(dataset_id)
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
                unsubscribe_token_key: unsubscribe_token
            }
        }
        response = requests.post(f'{novu_api_url}/subscribers', json=subscriber_data, headers=headers)
        if response.status_code != 201:
            raise Exception(f'Failed to create subscriber: {response.text}')

    elif response.status_code == 200:
        data = response.json().get('data', {}).get('data', {})
        data[unsubscribe_token_key] = unsubscribe_token
        subscriber_data = {
            'data': data
        }
        response = requests.put(f'{novu_api_url}/subscribers/{email}', json=subscriber_data, headers=headers)
        if response.status_code != 200:
            raise Exception(f'Failed to update subscriber: {response.text}')
    else:
        raise Exception(f'Error checking subscriber: {response.text}')

    topic_key = f'dataset-{dataset_id}'

    # Check if the topic exists
    response = requests.get(f'{novu_api_url}/topics/{topic_key}', headers=headers)

    if response.status_code == 404:
        # Topic doesn't exist; create a new one
        topic_data = {
            'key': topic_key,
            'name': f'Dataset {dataset_id} Updates'
        }
        response = requests.post(f'{novu_api_url}/topics', json=topic_data, headers=headers)
        if response.status_code != 201:
            raise Exception(f'Failed to create topic: {response.text}')

    elif response.status_code != 200:
        raise Exception(f'Error checking topic: {response.text}')

    add_subscriber_data = {
        'subscribers': [subscriber_id]
    }
    response = requests.post(f'{novu_api_url}/topics/{topic_key}/subscribers', json=add_subscriber_data,
                             headers=headers)

    if response.status_code != 200:
        raise Exception(f'Failed to add subscriber to topic: {response.text}')

    return {'message': f'You have successfully subscribed to notifications for this dataset.'}
