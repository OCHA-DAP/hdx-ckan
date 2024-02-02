import logging as logging

import ckan.plugins.toolkit as tk
import ckanext.hdx_users.helpers.mailer as hdx_mailer
import ckanext.hdx_users.model as umodel

from typing import Dict

log = logging.getLogger(__name__)

NotFound = tk.ObjectNotFound
config = tk.config
h = tk.h

def token_show(context, user):
    id = user.get('id')
    token_obj = umodel.ValidationToken.get(user_id=id)
    if token_obj is None:
        raise NotFound
    return token_obj.as_dict()


def get_user_id_from_token(token: str) -> str:
    token_obj = umodel.ValidationToken.get_by_token(token=token)
    if token_obj is None:
        raise NotFound
    return token_obj.user_id


def send_validation_email(user: Dict, token: Dict, subject: str, template_path: str) -> bool:
    validation_link = h.url_for('hdx_user_register.validate', token=token['token'], qualified=True)
    # link = '{0}{1}'
    email_data = {
        'validation_link': validation_link
    }
    try:
        hdx_mailer.mail_recipient([{'email': user['email']}], subject, email_data, footer=user['email'],
                                  snippet=template_path)
        return True
    except Exception as e:
        error_summary = str(e)
        log.error(error_summary)
        return False
