import logging

import ckan.plugins.toolkit as tk
import ckan.model as model

from ckanext.hdx_users.general_token_model import generate_new_token_obj, validate_token, ObjectType, TokenType, \
    HDXGeneralToken

log = logging.getLogger(__name__)

h = tk.h
config = tk.config
get_action = tk.get_action


def generate_email_validation_token(email: str, dataset_id: str) -> HDXGeneralToken:
    return generate_new_token_obj(model.Session, TokenType.EMAIL_VALIDATION_FOR_DATASET, email,
                                  object_type=ObjectType.DATASET, object_id=dataset_id)


def generate_unsubscribe_token(email: str, dataset_id: str) -> HDXGeneralToken:
    return generate_new_token_obj(model.Session, TokenType.UNSUBSCRIBE_FOR_DATASET, email,
                                  object_type=ObjectType.DATASET, object_id=dataset_id)


def verify_email_validation_token(token: str) -> HDXGeneralToken:
    return validate_token(model.Session, token, TokenType.EMAIL_VALIDATION_FOR_DATASET)


def verify_unsubscribe_token(token: str, inactivate: bool = True) -> HDXGeneralToken:
    return validate_token(model.Session, token, TokenType.UNSUBSCRIBE_FOR_DATASET, inactivate=inactivate)
