import logging
import json

import ckan.plugins.toolkit as tk
import ckan.model as model
import ckanext.hdx_users.helpers.helpers as usr_h
import ckanext.hdx_users.helpers.mailer as hdx_mailer

from flask import Blueprint, make_response
from ckan.lib.mailer import MailerException
from ckan.types import Response, DataDict
from ckan.views.api import CONTENT_TYPES

from ckanext.hdx_theme.util.mail import hdx_validate_email
from ckanext.hdx_users.general_token_model import generate_new_token_obj, validate_token, ObjectType, TokenType, HDXGeneralToken

_h = tk.h

log = logging.getLogger(__name__)

hdx_notifications = Blueprint(u'hdx_notifications', __name__, url_prefix=u'/notifications')


def _verify_email_validation_token(token: str) -> HDXGeneralToken:
    return validate_token(model.Session, token, TokenType.EMAIL_VALIDATION_FOR_DATASET)

def _verify_unsubscribe_token(token: str) -> HDXGeneralToken:
    return validate_token(model.Session, token, TokenType.UNSUBSCRIBE_FOR_DATASET)


def subscribe_to_dataset() -> Response:
    # Get parameters from the URL
    # email = tk.request.args.get('email')
    # dataset_id = tk.request.args.get('dataset_id')
    token = tk.request.args.get('token')

    dataset_list_url = tk.url_for('dataset.search')
    token_obj = _verify_email_validation_token(token)
    if not token_obj:
        _h.flash_error('Your token is invalid or has expired. Please try to subscribe again.')
        return tk.redirect_to(dataset_list_url)

    email = token_obj.user_id
    dataset_id = token_obj.object_id
    if not email or not dataset_id:
        _h.flash_error('Couldn\'t find required parameters: email and dataset_id.')
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
    token_valid = _verify_unsubscribe_token(token)
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


def subscription_confirmation() -> Response:
    email = tk.request.form.get('email')
    dataset_id = tk.request.form.get('dataset_id')

    try:
        usr_h.is_valid_captcha(tk.request.form.get('g-recaptcha-response'))

        if not email:
            raise tk.Invalid(tk._('Email address is missing'))
        hdx_validate_email(email)

        token_obj = generate_new_token_obj(model.Session, TokenType.EMAIL_VALIDATION_FOR_DATASET, email, object_type=ObjectType.DATASET, object_id=dataset_id)

        subject = u'Please verify your email address'
        verify_email_link = _h.url_for(
            'hdx_notifications.subscribe_to_dataset',
            email=email, dataset_id=dataset_id, token=token_obj.token, qualified=True
        )
        email_data = {
            'verify_email_link': verify_email_link
        }
        hdx_mailer.mail_recipient([{'email': email}], subject, email_data, footer=None,
                                  snippet='email/content/notification_platform/verify_email.html')

    except tk.ValidationError as e:
        return _build_json_response(
            {
                'success': False,
                'error': {
                    'message': e.error_summary
                }
            }
        )
    except tk.Invalid as e:
        return _build_json_response(
            {
                'success': False,
                'error': {
                    'message': e.error
                }
            }
        )
    except Exception as e:
        log.error(e)
        return _build_json_response(
            {
                'success': False,
                'error': {
                    'message': str(e)
                }
            }
        )
    except MailerException as e:
        log.error(e)
        return _build_json_response(
            {
                'success': False,
                'error': {
                    'message': u'Error sending the confirmation email, please try again.'
                }
            }
        )
    return _build_json_response({'success': True})


def _build_json_response(data_dict: DataDict, status=200):
    headers = {
        'Content-Type': CONTENT_TYPES['json'],
    }
    body = json.dumps(data_dict)
    response = make_response((body, status, headers))
    return response


hdx_notifications.add_url_rule(u'/subscribe-to-dataset', view_func=subscribe_to_dataset)
hdx_notifications.add_url_rule(u'/unsubscribe-from-dataset', view_func=unsubscribe_from_dataset)
hdx_notifications.add_url_rule(u'/subscription-confirmation', view_func=subscription_confirmation, methods=['POST'])
