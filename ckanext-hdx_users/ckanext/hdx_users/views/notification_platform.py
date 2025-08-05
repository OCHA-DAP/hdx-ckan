import logging
import json
from typing import Dict

from ckanext.hdx_users.general_token_model import get_by_type_and_user_id_and_object, HDXGeneralToken, TokenType
from ckanext.hdx_users.notifications_subscription_model import EventType

import ckan.plugins.toolkit as tk
import ckan.model as model
import ckanext.hdx_users.helpers.helpers as usr_h
import ckanext.hdx_users.helpers.mailer as hdx_mailer

from flask import Blueprint, make_response
from ckan.common import current_user
from ckan.lib.mailer import MailerException
from ckan.types import Response, DataDict, Context
from ckan.views.api import CONTENT_TYPES

from ckanext.hdx_theme.util.mail import hdx_validate_email
from ckanext.hdx_users.controller_logic import notification_platform_logic
from ckanext.hdx_users.helpers.analytics import EmailValidationAnalyticsSender
from ckanext.hdx_users.helpers.constants import NOTIFICATION_PLATFORM_EVENT_TYPE_EXTRAS_KEY
from ckanext.hdx_users.notifications_subscription_model import ObjectType

from hashlib import md5

_h = tk.h
abort = tk.abort
request = tk.request

log = logging.getLogger(__name__)

hdx_notifications = Blueprint(u'hdx_notifications', __name__, url_prefix=u'/notifications')

def subscribe_to_object() -> Response:
    """
    Subscribe to an object (dataset, organization, group, crisis) for notifications as a guest user
    using an email validation token.
    There are 2 cases:
    1. User has an account either shadow or active - we need the email validation token to find the
       user and to register the new subscription
    2. User doesn't have an account - we need the email validation token to create a shadow account
       and to register the new subscription
    """



    dataset_list_url = tk.url_for('dataset.search')
    # we don't want to run this for 'HEAD' requests or for requests that don't come from a browser
    if request.user_agent.string.strip() and request.method == 'GET':
        token = request.args.get('token')
        try:
            token_obj = notification_platform_logic.verify_email_validation_token(token)
        except Exception as e:
            _h.flash_error('Your token is invalid. Your email address might have already been validated.')
            EmailValidationAnalyticsSender('notification platform', False, '').send_to_queue()
            return tk.redirect_to(dataset_list_url)

        email = token_obj.user_id
        object_type = token_obj.object_type
        object = token_obj.object_id
        event_type = token_obj.extras.get(NOTIFICATION_PLATFORM_EVENT_TYPE_EXTRAS_KEY, EventType.DATASET_UPDATED.value)
        if not email or not object:
            _h.flash_error('Couldn\'t find required parameters: email and dataset_id.')
            EmailValidationAnalyticsSender('notification platform', False, '').send_to_queue()
            return tk.redirect_to(dataset_list_url)

        # create shadow account if needed
        context: Context = {'model': model,'session': model.Session, 'ignore_auth': True}
        user_dict = tk.get_action('hdx_shadow_user_create')(context, {'email': email})
        user_id = user_dict['id']
    else:
        return abort(404, 'Page not found')

    data_dict = {
        'user_id': user_id,
        'object': object,
        'object_type': object_type,
        'event_type': event_type,
        'email': email,
    }
    try:
        tk.get_action('hdx_notifications_subscription_create')(context, data_dict)
        _h.flash_success(tk._(
            u'You have successfully set up email notifications. These will be sent to {0} when there '
            u'is an update.'.format(
                current_user.email)))
    except tk.ValidationError as e:
        msg = e.error_dict.get('message', str(e))
        _h.flash_error(msg)
    except Exception as e:
        log.error('An exception occurred:' + str(e))
        _h.flash_error('An error occurred: ' + str(e))

    try:
        unsubscribe_token = get_by_type_and_user_id_and_object(TokenType.UNSUBSCRIBE_FOR_NOTIFICATION, user_id,
                                                               ObjectType(object_type), object)
        redirect_url = _generate_url_for(object_type, object, False, unsubscribe_token)
    except Exception as e:
        log.error('An exception occurred:' + str(e))
        return abort(500, 'An error occurred')

    return tk.redirect_to(redirect_url)


# def subscribe_to_dataset() -> Response:
#     # Get parameters from the URL
#     # email = tk.request.args.get('email')
#     # dataset_id = tk.request.args.get('dataset_id')
#
#     if request.user_agent.string.strip() and request.method == 'GET':
#         # we don't want to run this for 'HEAD' requests or for requests that don't come from a browser
#         token = tk.request.args.get('token')
#
#         dataset_list_url = tk.url_for('dataset.search')
#         try:
#             token_obj = notification_platform_logic.verify_email_validation_token(token)
#         except Exception as e:
#             _h.flash_error('Your token is invalid. Your email address might have already been validated.')
#             EmailValidationAnalyticsSender('notification platform', False, '').send_to_queue()
#             return tk.redirect_to(dataset_list_url)
#
#         email = token_obj.user_id
#         dataset_id = token_obj.object_id
#         if not email or not dataset_id:
#             _h.flash_error('Couldn\'t find required parameters: email and dataset_id.')
#             EmailValidationAnalyticsSender('notification platform', False, '').send_to_queue()
#             return tk.redirect_to(dataset_list_url)
#
#         context = {'ignore_auth': True}
#
#         try:
#             unsubscribe_token = notification_platform_logic.get_or_generate_unsubscribe_token(email, dataset_id)
#             data_dict = {
#                 'email': email,
#                 'dataset_id': dataset_id,
#                 'unsubscribe_token': unsubscribe_token.token,
#             }
#             result = _add_notification_subscription(context, data_dict)
#             _h.flash_success(tk._(
#                 u'You have successfully set up email notifications for this dataset. These will be sent to {0} when the '
#                 u'dataset is updated on HDX.'.format(
#                     email)))
#         except tk.ValidationError as e:
#             log.error('An exception occurred:' + str(e))
#             _h.flash_error(str(e))
#         except Exception as e:
#             log.error('An exception occurred:' + str(e))
#             _h.flash_error('An error occurred: ' + str(e))
#
#         email_hash = md5(email.strip().lower().encode('utf8')).hexdigest()
#         EmailValidationAnalyticsSender('notification platform', True, email_hash).send_to_queue()
#
#         # Redirect to the dataset page
#         dataset_url = tk.url_for('dataset.read', id=dataset_id, came_from='notification_platform_subscription',
#                                  u=data_dict.get('unsubscribe_token'))
#         return tk.redirect_to(dataset_url)
#     return abort(404, 'Page not found')

def _generate_url_for(object_type: str, object: str, external: bool = False, unsubscribe_token: HDXGeneralToken = None) -> str:
    if object_type == ObjectType.DATASET.value:
        endpoint = 'dataset.read'
    elif object_type == ObjectType.ORGANIZATION.value:
        endpoint = 'organization.read'
    elif object_type == ObjectType.GROUP.value:
        endpoint = 'group.read'
    elif object_type == ObjectType.CRISIS.value:
        page_dict = tk.get_action('page_show')({}, {'id': object})
        if page_dict.get('type') == 'event':
            endpoint = 'hdx_light_event.read_light_event'
        else:
            endpoint = 'hdx_light_dashboard.read_light_dashboard'
    else:
        raise tk.ValidationError(f'Invalid object_type: {object_type}')

    if unsubscribe_token:
        return tk.url_for(endpoint, id=object, _came_from='notification_platform_subscription',
                          _u=unsubscribe_token.token, _external=external)

    return tk.url_for(endpoint, id=object, _external=external)


def subscription_confirmation() -> Response:
    email = tk.request.form.get('email')
    object_id = tk.request.form.get('object_id')
    object_type_str = tk.request.form.get('object_type')
    object_type = ObjectType(object_type_str)
    # dataset_updates = tk.request.form.get('dataset_updates') == 'true'
    dataset_updates = False

    json_response_dict: Dict[str: any] = {
        'success': True
    }
    error_message = None
    http_status = 200

    try:

        if not current_user.is_authenticated:
            usr_h.is_valid_captcha(tk.request.form.get('g-recaptcha-response'))

            if not email:
                raise tk.Invalid(tk._('Email address is missing'))
            hdx_validate_email(email)

            action = None
            if object_type == ObjectType.DATASET.value:
                action = 'package_show'
            elif object_type == ObjectType.GROUP.value:
                action = 'group_show'
            elif object_type == ObjectType.ORGANIZATION.value:
                action = 'organization_show'
            elif object_type == ObjectType.CRISIS.value:
                action = 'page_show'

            try:
                context: Context = {}
                object_dict = tk.get_action(action)(context, {'id': object_id})
            except tk.ObjectNotFound:
                raise tk.ValidationError(f'{object_type.value} {object_id} does not exist')
            except Exception as e:
                log.error(f'Error retrieving target or user: {e}')
                raise e

            extras = {
                NOTIFICATION_PLATFORM_EVENT_TYPE_EXTRAS_KEY: EventType.DATASET_UPDATED.value if dataset_updates else EventType.NEW_DATASET_ADDED.value
            }
            token_obj = notification_platform_logic.get_or_generate_email_validation_token(email, object_type,
                                                                                           object_dict['id'],
                                                                                           object_dict, extras)

            subject = u'Please verify your email address'
            verify_email_link = _h.url_for(
                'hdx_notifications.subscribe_to_object',
                token=token_obj.token, qualified=True
            )
            email_data = {
                'verify_email_link': verify_email_link,
                'object_title': object_dict.get('title'),
                'object_id': object_id,
                'object_link': _generate_url_for(object_type.value, object_id, True),
                'object_type': object_type.value,
                'dataset_updates': dataset_updates,
            }
            hdx_mailer.mail_recipient([{'email': email}], subject, email_data, footer=None,
                                      snippet='email/content/notification_platform/verify_email.html')

        # user is authenticated
        else:
            context: Context = {'session': model.Session, 'user': current_user.name}

            # data_dict = {
            #     'email': email,
            #     'object_id': object_id,
            #     'object_type': object_type,
            #     'unsubscribe_token': unsubscribe_token.token,
            # }
            # result = _add_notification_subscription(context, data_dict)

            data_dict = {
                'user_id': current_user.id,
                'object': object_id,
                'object_type': object_type,
                'event_type': EventType.DATASET_UPDATED.value if dataset_updates else EventType.NEW_DATASET_ADDED.value,
            }

            subscription = tk.get_action('hdx_notifications_subscription_create')(context, data_dict)

            email = current_user.email

            email_hash = md5(email.strip().lower().encode('utf8')).hexdigest()
            EmailValidationAnalyticsSender('notification platform', True, email_hash).send_to_queue()

            json_response_dict['unsubscribe_token'] = subscription.get('unsubscribe_token')

    except tk.ValidationError as e:
        http_status = 400
        error_message = e.error_dict.get('message')
    except tk.Invalid as e:
        http_status = 400
        error_message = e.error
    except MailerException as e:
        http_status = 500
        log.error(e)
        error_message = 'Error sending the confirmation email, please try again.'
    except Exception as e:
        http_status = 500
        log.error(e)
        error_message = str(e)
    if error_message:
        json_response_dict = {
            'success': False,
            'error': {
                'message': error_message
            }
        }
    return _build_json_response(json_response_dict, status=http_status)


def unsubscribe_confirmation() -> Response:
    token = tk.request.form.get('token')

    try:
        # We let anybody (guest users included) that has the token to unsubscribe, so we ignore auth
        context: Context = {'ignore_auth': True}
        data_dict = {'token': token}
        result = tk.get_action('hdx_notifications_subscription_delete')(context, data_dict)

    except tk.ValidationError as e:
        log.error('An exception occurred:' + str(e))
        return _build_json_response(
            {
                'success': False,
                'error': {
                    'message': 'An exception occurred:' + str(e)
                }
            }
        )
    except Exception as e:
        log.error('An exception occurred:' + str(e))
        return _build_json_response(
            {
                'success': False,
                'error': {
                    'message': 'An error occurred: ' + str(e)
                }
            }
        )
    return _build_json_response({'success': True})


# def _delete_notification_subscription(context: Context, data_dict: DataDict) -> DataDict:
#     result = tk.get_action('hdx_delete_notification_subscription')(context, data_dict)
#     return result

def _build_json_response(data_dict: DataDict, status=200):
    headers = {
        'Content-Type': CONTENT_TYPES['json'],
    }
    body = json.dumps(data_dict)
    response = make_response((body, status, headers))
    return response


# hdx_notifications.add_url_rule(u'/subscribe-to-dataset', view_func=subscribe_to_dataset)
hdx_notifications.add_url_rule(u'/subscribe-to-object', view_func=subscribe_to_object, methods=['GET', 'POST'])
hdx_notifications.add_url_rule(u'/subscription-confirmation', view_func=subscription_confirmation, methods=['POST'])
hdx_notifications.add_url_rule(u'/unsubscribe-confirmation', view_func=unsubscribe_confirmation, methods=['POST'])
