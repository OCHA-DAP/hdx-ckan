import logging

import ckan.plugins.toolkit as tk
import ckan.model as model

from ckanext.hdx_users.general_token_model import generate_new_token_obj, validate_token, ObjectType, TokenType, \
    HDXGeneralToken, get_by_type_and_user_id_and_object
from ckanext.hdx_users.helpers.notification_platform import check_notifications_enabled_for_dataset

log = logging.getLogger(__name__)

h = tk.h
config = tk.config
get_action = tk.get_action


def get_or_generate_email_validation_token(email: str, dataset_id: str) -> HDXGeneralToken:
    dataset_supports_notifications = check_notifications_enabled_for_dataset(dataset_id)
    if dataset_supports_notifications:
        email_validation_token = get_by_type_and_user_id_and_object(TokenType.EMAIL_VALIDATION_FOR_DATASET, email,
                                                                        ObjectType.DATASET, dataset_id)
        if email_validation_token:
            return email_validation_token
        else:
            return generate_new_token_obj(model.Session, TokenType.EMAIL_VALIDATION_FOR_DATASET, email,
                                      object_type=ObjectType.DATASET, object_id=dataset_id)
    else:
        log.warning(f'Tried to generate token for dataset {dataset_id} but dataset does not support notifications')
        raise Exception(f'Dataset {dataset_id} does not support notifications')


def get_or_generate_unsubscribe_token(email: str, dataset_id: str) -> HDXGeneralToken:
    existing_unsubscribe_token = get_by_type_and_user_id_and_object(TokenType.UNSUBSCRIBE_FOR_DATASET, email,
                                                                    ObjectType.DATASET, dataset_id)
    if existing_unsubscribe_token:
        return existing_unsubscribe_token
    else:
        return generate_new_token_obj(model.Session, TokenType.UNSUBSCRIBE_FOR_DATASET, email,
                                  object_type=ObjectType.DATASET, object_id=dataset_id)


def verify_email_validation_token(token: str) -> HDXGeneralToken:
    return validate_token(model.Session, token, TokenType.EMAIL_VALIDATION_FOR_DATASET)


def verify_unsubscribe_token(token: str, inactivate: bool = True) -> HDXGeneralToken:
    return validate_token(model.Session, token, TokenType.UNSUBSCRIBE_FOR_DATASET, inactivate=inactivate)
