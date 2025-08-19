import logging

from typing import Any, Optional, Dict

import ckan.plugins.toolkit as tk
import ckan.model as model
from ckan.types import AlchemySession

from ckanext.hdx_theme.helpers.helpers import hdx_supports_notifications

from ckanext.hdx_users.general_token_model import generate_new_token_obj, validate_token, ObjectType, TokenType, \
    HDXGeneralToken, get_by_type_and_user_id_and_object, get_by_token_with_checks

log = logging.getLogger(__name__)

h = tk.h
config = tk.config
get_action = tk.get_action


def get_or_generate_email_validation_token(email: str, object_type: ObjectType, object_id: str,
                                           object_dict: Optional[dict[str, Any]] = None,
                                           extras: Optional[Dict] = None) -> HDXGeneralToken:
    object_supports_notifications = hdx_supports_notifications(object_type, object_id, object_dict)
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
            f'Tried to generate token for {object_type.value} {object_id} but it does not support notifications')
        raise Exception(f'{object_type.display_name} {object_id} does not support notifications')


def get_or_generate_unsubscribe_token(session: AlchemySession, user_id: str, object_type: ObjectType, object_id: str,
                                      extras: Optional[Dict] = None, commit_tx: bool = True) -> HDXGeneralToken:
    existing_unsubscribe_token = get_by_type_and_user_id_and_object(TokenType.UNSUBSCRIBE_FOR_NOTIFICATION, user_id,
                                                                    object_type, object_id)
    if existing_unsubscribe_token:
        return existing_unsubscribe_token
    else:
        return generate_new_token_obj(session, TokenType.UNSUBSCRIBE_FOR_NOTIFICATION, user_id,
                                      object_type=object_type, object_id=object_id, extras=extras, commit_tx=commit_tx)


def verify_email_validation_token(token: str) -> HDXGeneralToken:
    return validate_token(model.Session, token, TokenType.EMAIL_VALIDATION_FOR_NOTIFICATION, True)


def get_unsubscribe_token(token: str) -> HDXGeneralToken:
    return get_by_token_with_checks(token, TokenType.UNSUBSCRIBE_FOR_NOTIFICATION)
