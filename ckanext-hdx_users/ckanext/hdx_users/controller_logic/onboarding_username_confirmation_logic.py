import logging

import ckan.plugins.toolkit as tk

import ckanext.hdx_users.helpers.mailer as hdx_mailer

from ckan.types import ActionResult


log = logging.getLogger(__name__)

h = tk.h

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
