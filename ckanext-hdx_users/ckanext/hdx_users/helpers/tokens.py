import logging as logging

import ckan.plugins.toolkit as tk
import ckan.model as model

import ckanext.hdx_users.helpers.mailer as hdx_mailer
import ckanext.hdx_users.model as umodel

from typing import Dict, Union
from ckan.types import Context
from ckanext.hdx_users.helpers.reset_password import make_key

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


def refresh_token(context: Context, data_dict: Dict) -> Dict:
    token = data_dict.get('token')
    token_obj = umodel.ValidationToken.get_by_token(token=token)
    if token_obj is None:
        raise NotFound
    token_obj.token = make_key()
    context['session'].commit()
    return token_obj.as_dict()


def activate_user_and_disable_token(context: Context, data_dict: Dict) -> Union[Dict, None]:
    session = context['session']
    try:
        token = data_dict.get('token')
        token_obj = umodel.ValidationToken.get_by_token(token=token)
        user_obj = model.User.get(token_obj.user_id)
        user_obj.state = 'active'
        token_obj.valid = True
        session.commit()
        context['user'] = user_obj.name
        return tk.get_action('user_show')(context, {'id': token_obj.user_id})
    except Exception as e:
        log.error(str(e))
        session.rollback()
    return None

def send_validation_email(user: Dict, token: Dict, subject: str, template_path: str, validation_link: str) -> bool:
    # link = '{0}{1}'
    email_data = {
        'user_fullname': user.get('fullname'),
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


def is_user_validated_and_token_disabled(user_dict: Dict):
    token = token_show({}, user_dict)
    # valid is False when the token was not used yet
    return user_dict.get('state') == 'active' and token['valid'] is True
