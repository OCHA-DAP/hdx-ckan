import logging

from typing import Optional, Dict

import ckan.plugins.toolkit as tk
import ckan.model as model

from ckanext.hdx_users.general_token_model import generate_new_token_obj, validate_token, ObjectType, TokenType, \
    HDXGeneralToken, get_by_type_and_user_id_and_object

log = logging.getLogger(__name__)

h = tk.h
config = tk.config
get_action = tk.get_action


def get_or_generate_email_validation_token(email: str, object_type: ObjectType, object_id: str,
                                           extras: Optional[Dict] = None) -> HDXGeneralToken:
    object_supports_notifications = h.hdx_supports_notifications(object_type, object_id)
    if object_supports_notifications:
        email_validation_token = get_by_type_and_user_id_and_object(TokenType.EMAIL_VALIDATION_FOR_NOTIFICATION, email,
                                                                    object_type, object_id)
        if email_validation_token:
            return email_validation_token
        else:
            return generate_new_token_obj(model.Session, TokenType.EMAIL_VALIDATION_FOR_NOTIFICATION, email,
                                          object_type=object_type, object_id=object_id, extras=extras)
    else:
        log.warning(
            f'Tried to generate token for {object_type} {object_id} but {object_type} does not support notifications')
        raise Exception(f'{object_type} {object_id} does not support notifications')


def get_or_generate_unsubscribe_token(email: str, object_type: ObjectType, object_id: str,
                                      extras: Optional[Dict] = None) -> HDXGeneralToken:
    existing_unsubscribe_token = get_by_type_and_user_id_and_object(TokenType.UNSUBSCRIBE_FOR_NOTIFICATION, email,
                                                                    object_type, object_id)
    if existing_unsubscribe_token:
        return existing_unsubscribe_token
    else:
        return generate_new_token_obj(model.Session, TokenType.UNSUBSCRIBE_FOR_NOTIFICATION, email,
                                      object_type=object_type, object_id=object_id, extras=extras)


def verify_email_validation_token(token: str) -> HDXGeneralToken:
    return validate_token(model.Session, token, TokenType.EMAIL_VALIDATION_FOR_NOTIFICATION)


def verify_unsubscribe_token(token: str, inactivate: bool = True) -> HDXGeneralToken:
    return validate_token(model.Session, token, TokenType.UNSUBSCRIBE_FOR_NOTIFICATION, inactivate=inactivate)
