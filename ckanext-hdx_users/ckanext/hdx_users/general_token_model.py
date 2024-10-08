import datetime
import logging

from enum import Enum
from typing import Optional, Dict, List

from sqlalchemy import Column, types
from sqlalchemy.dialects.postgresql import JSONB

import ckan.model.meta as meta
# import ckan.model.domain_object as domain_object
import ckan.model.types as ckan_types
import ckan.plugins.toolkit as tk
from ckan.lib.mailer import make_key as ckan_make_key
from ckan.types import AlchemySession


log = logging.getLogger(__name__)


class HDXGeneralToken(tk.BaseModel):
    __tablename__ = 'hdx_general_token'

    id = Column(
        'id', types.UnicodeText, primary_key=True, default=ckan_types.make_uuid
    )
    token = Column('token', types.UnicodeText, default=ckan_make_key, index=True, unique=True, nullable=False)
    token_type = Column('token_type', types.UnicodeText, index=True, nullable=False)
    state = Column('state', types.UnicodeText, default='active', index=True, nullable=False) # active / inactive
    user_id = Column('user_id', types.UnicodeText, index=True, nullable=False)
    object_type = Column('object_type', types.UnicodeText, nullable=True) # dataset
    object_id = Column('object_id', types.UnicodeText, nullable=True)
    created = Column('created', types.DateTime, default=datetime.datetime.now, nullable=False)
    expires = Column('expires', types.DateTime, nullable=True)
    extras = Column('extras', JSONB, nullable=True)


class State(str, Enum):
    ACTIVE = 'active'
    INACTIVE = 'inactive'


class TokenType(str, Enum):
    EMAIL_VALIDATION_FOR_DATASET = 'email-validation-for-dataset'
    UNSUBSCRIBE_FOR_DATASET = 'unsubscribe-for-dataset'


class ObjectType(str, Enum):
    DATASET = 'dataset'


def generate_new_token_obj(session: AlchemySession,
                       token_type: TokenType,
                       user_id: str,
                       state: State = State.ACTIVE,
                       object_type: Optional[ObjectType] = None,
                       object_id: Optional[str] = None,
                       extras: Optional[Dict] = None,
                       days_till_expiration: Optional[int] = None) -> HDXGeneralToken:

    new_token = HDXGeneralToken(
        token_type=token_type.value,
        user_id=user_id,
        state=state.value,
    )
    if extras:
        new_token.extras = extras
    if object_type:
        new_token.object_type = object_type.value
        new_token.object_id = object_id
    if days_till_expiration:
        new_token.expires = datetime.datetime.now() + datetime.timedelta(days=days_till_expiration)

    session.add(new_token)
    session.commit()
    return new_token


def get(token_id: str) -> Optional[HDXGeneralToken]:
    if not token_id:
        return None

    return meta.Session.query(HDXGeneralToken).get(token_id)


def get_by_token(token: str) -> Optional[HDXGeneralToken]:
    if not token:
        return None

    return meta.Session.query(HDXGeneralToken).filter(HDXGeneralToken.token == token).first()


def get_by_type_and_user_id(token_type: TokenType, user_id: str) -> Optional[List[HDXGeneralToken]]:
    if not token_type or not user_id:
        return None

    return meta.Session.query(HDXGeneralToken) \
            .filter(HDXGeneralToken.token_type == token_type.value) \
            .filter(HDXGeneralToken.user_id == user_id) \
            .all()


def get_by_type_and_user_id_and_object(token_type: TokenType, user_id: str,
                                       object_type: ObjectType, object_id: str) -> Optional[HDXGeneralToken]:
    if not token_type or not user_id or not object_type or not object_id:
        return None

    return meta.Session.query(HDXGeneralToken) \
        .filter(HDXGeneralToken.token_type == token_type.value) \
        .filter(HDXGeneralToken.user_id == user_id) \
        .filter(HDXGeneralToken.object_type == object_type.value) \
        .filter(HDXGeneralToken.object_id == object_id) \
        .filter(HDXGeneralToken.state == 'active') \
        .first()


def validate_token(session: AlchemySession, token: str, token_type: TokenType, inactivate=True) -> HDXGeneralToken:
    token_obj = get_by_token(token)
    if not token_obj:
        log.warning(f'Token object not found for token string {token}')
        raise Exception(f'Token object not found for given token string')

    if token_obj.state != State.ACTIVE.value:
        log.warning(f'Token object found for token string {token} but it is inactive')
        raise Exception(f'Token object found for given token string but it is inactive')

    if token_obj.token_type != token_type:
        log.warning(f'Token object found for token string {token} '
                    f'but it is of type {token_obj.token_type} instead of {token_type}')
        raise Exception(f'Token object found for given token string but the type is wrong')

    # if token_obj.user_id != user_id:
    #     log.warning(f'Token object found for token string {token} '
    #                 f'but it has user id {token_obj.user_id} instead of {user_id}')
    #     raise Exception(f'Token object found for given token string but the user id is wrong')
    #
    # if token_obj.object_type and token_obj.object_type != object_type:
    #     log.warning(f'Token object found for token string {token} but it has object type {token_obj.object_type} '
    #                 f'instead of {object_type}')
    #     raise Exception(f'Token object found for given token string but it had wrong object type')
    #
    # if token_obj.object_type and token_obj.object_id and token_obj.object_id != object_id:
    #     log.warning(f'Token object found for token string {token} but it has object id {token_obj.object_id} '
    #                 f'instead of {object_id}')
    #     raise Exception(f'Token object found for given token string but it had wrong object id')

    if inactivate:
        token_obj.state = State.INACTIVE.value

    session.add(token_obj)
    session.commit()

    return token_obj
