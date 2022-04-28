import logging as logging

import ckan.plugins.toolkit as tk
import ckanext.hdx_users.helpers.mailer as hdx_mailer
import ckanext.hdx_users.model as umodel

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


def token_show_by_id(context, data_dict):
    token = data_dict.get('token', None)
    token_obj = umodel.ValidationToken.get_by_token(token=token)
    if token_obj is None:
        raise NotFound
    return token_obj.as_dict()


def token_update(context, data_dict):
    token = data_dict.get('token')
    token_obj = umodel.ValidationToken.get_by_token(token=token)
    if token_obj is None:
        raise NotFound
    session = context["session"]
    token_obj.valid = True
    session.add(token_obj)
    session.commit()
    return token_obj.as_dict()


def send_validation_email(user, token):
    validation_link = h.url_for('hdx_user_register.validate', token=token['token'], qualified=True)
    # link = '{0}{1}'
    subject = "Complete your HDX registration"
    email_data = {
        'validation_link': validation_link
    }
    try:
        print(validation_link)
        hdx_mailer.mail_recipient([{'email': user['email']}], subject, email_data, footer=user['email'],
                                  snippet='email/content/onboarding_email_validation.html')
        return True
    except Exception as e:
        error_summary = str(e)
        log.error(error_summary)
        return False
