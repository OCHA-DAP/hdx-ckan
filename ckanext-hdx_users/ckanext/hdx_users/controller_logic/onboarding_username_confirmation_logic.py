import logging

import ckan.plugins.toolkit as tk
import ckan.model as model

import ckanext.hdx_users.helpers.mailer as hdx_mailer

from ckan.types import ActionResult, DataDict

from ckanext.hdx_users.helpers.constants import (
    ONBOARDING_MAILCHIMP_OPTIN_KEY
)
from mailchimp3 import MailChimp

log = logging.getLogger(__name__)

h = tk.h
config = tk.config
get_action = tk.get_action


def send_username_confirmation_email(user_dict: ActionResult.UserShow) -> bool:
    subject = h.HDX_CONST('UI_CONSTANTS')['ONBOARDING']['EMAIL_SUBJECTS']['EMAIL_USERNAME_CONFIRMATION']

    email_data = {
        'user_fullname': user_dict.get('fullname'),
        'username': user_dict['name'],
        'login_link': h.url_for('hdx_user_auth.new_login')
    }
    try:
        hdx_mailer.mail_recipient([{'email': user_dict['email']}], subject, email_data, footer=user_dict['email'],
                                  snippet='email/content/onboarding/email_username_confirmation.html')
        return True
    except Exception as e:
        error_summary = str(e)
        log.error(error_summary)
        return False


def subscribe_user_to_mailchimp(user_dict: ActionResult.UserShow) -> bool:
    """
    Subscribes a user to Mailchimp newsletter lists if they have opted in.

    Args:
        user_dict (dict): A dictionary containing user data.

    Returns:
        bool: True if the user was successfully subscribed, False otherwise.
    """
    if _is_subscribed_to_emails(user_dict) and 'email' in user_dict:
        newsletter_list_id = config.get('hdx.mailchimp.list.newsletter')
        new_user_list_id = config.get('hdx.mailchimp.list.newuser')

        if newsletter_list_id or new_user_list_id:
            if newsletter_list_id:
                """
                to retrieve interests ID, follow these steps:
                1. use `mailchimp.lists.interest_categories.all(list_id)` to obtain the "Area(s) of Interest"
                category ID
                2. once you have the category ID, use `mailchimp.lists.interest_categories.interests.all(list_id,
                category_id)` to fetch category interests (options
                """
                ds_interest_id = config.get('hdx.mailchimp.interest.data_services')
                _subscribe_to_mailchimp_list(user_dict['email'], newsletter_list_id, {ds_interest_id: True})

            if new_user_list_id:
                _subscribe_to_mailchimp_list(user_dict['email'], new_user_list_id)

            return True

    return False


def _subscribe_to_mailchimp_list(email: str, list_id: str, interests: DataDict = None):
    """
    Subscribes a user to a Mailchimp list with optional interests.

    Args:
        email (str): The email address of the user to subscribe.
        list_id (str): The ID of the Mailchimp list.
        interests (dict, optional): Dictionary of interests and their statuses. Defaults to None.
    """
    data_dict = {'email_address': email, 'status': 'subscribed'}

    if interests:
        data_dict['interests'] = interests

    _mailchimp_create_member(data_dict, list_id)


def _is_subscribed_to_emails(user_data: DataDict) -> bool:
    """
    Checks if a user has opted in for email updates.

    Args:
        user_data (dict): A dictionary containing user data.

    Returns:
        bool: True if user has opted in, False otherwise.
    """
    context = {'session': model.Session, 'model': model, 'ignore_auth': True}
    ue_data_dict = {
        'user_id': user_data.get('id'),
        'key': ONBOARDING_MAILCHIMP_OPTIN_KEY
    }
    ue_extra = get_action('user_extra_value_by_key_show')(context, ue_data_dict)

    return ue_extra and ue_extra.get('hdx_onboarding_mailchimp_optin') == 'true'


def _mailchimp_create_member(data_dict: DataDict, list_id: str):
    """
    Creates a member in a Mailchimp list.

    Args:
        data_dict (dict): Dictionary containing member data.
        list_id (str): The ID of the Mailchimp list.
    """
    mailchimp = MailChimp(config.get('hdx.mailchimp.api.key'))
    try:
        mailchimp.ping.get()
        mailchimp.lists.members.create(list_id, data_dict)
    except Exception as ex:
        log.error(ex)
