import datetime
import logging
import uuid

from enum import Enum
from typing import Optional, Dict, List

from sqlalchemy import func, Column, types, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSONB

import ckan.model as model
import ckan.model.meta as meta
import ckan.model.types as ckan_types
import ckan.plugins.toolkit as tk

from ckan.types import AlchemySession, DataDict

from ckanext.hdx_users.general_token_model import ObjectType, State


log = logging.getLogger(__name__)


class HDXNotificationsSubscription(tk.BaseModel):
    __tablename__ = 'hdx_notifications_subscription'

    id = Column(
        'id', types.UnicodeText, primary_key=True, default=ckan_types.make_uuid
    )
    state = Column('state', types.UnicodeText, default='active', index=True, nullable=False)  # active / inactive
    user_id = Column('user_id', types.UnicodeText, ForeignKey('user.id'), index=True, nullable=False)
    object = Column('object', types.UnicodeText, nullable=False)
    object_type = Column('object_type', types.UnicodeText, nullable=False)
    event_type = Column('event_type', types.UnicodeText, nullable=False)
    query_params = Column('params', JSONB, nullable=True)
    created = Column('created', types.DateTime, default=datetime.datetime.now, nullable=False)
    updated = Column('updated', types.DateTime, default=datetime.datetime.now, index=True,
                     onupdate=datetime.datetime.now, nullable=False)
    unsubscribe_token_id = Column(
        'unsubscribe_token_id',
        types.UnicodeText, ForeignKey('hdx_general_token.id'), index=True, nullable=False, unique=True
    )

    __table_args__ = (
        Index(
            'ix_hdx_notifications_subscription_unique_active',
            'user_id', 'object', 'object_type',
            unique=True,
            postgresql_where=types.UnicodeText("state = 'active'")
        ),
    )


class EventType(str, Enum):
    NEW_DATASET_ADDED = 'new-dataset-added'
    DATASET_UPDATED = 'dataset-updated'


def generate_notifications_subscription(
    session: AlchemySession,
    user_id: str,
    object_type: ObjectType,
    object: str,
    event_type: EventType,
    unsubscribe_token_id: str,
    query_params: Optional[Dict] = None,
    commit_tx: bool = True,
) -> HDXNotificationsSubscription:
    subscription = HDXNotificationsSubscription(
        user_id=user_id,
        object=object,
        object_type=object_type.value,
        event_type=event_type.value,
        unsubscribe_token_id=unsubscribe_token_id,
        query_params=query_params
    )
    session.add(subscription)
    if commit_tx:
        session.commit()
    return subscription

def notifications_subscription_dictize(subscription: HDXNotificationsSubscription) -> Dict:
    return {
        'id': subscription.id,
        'user_id': subscription.user_id,
        'object': subscription.object,
        'object_type': subscription.object_type,
        'event_type': subscription.event_type,
        'query_params': subscription.query_params,
        'created': subscription.created.isoformat(),
        'updated': subscription.updated.isoformat(),
        'state': subscription.state,
    }


def list_notifications_subscriptions(session: AlchemySession, user_id: Optional[str] = None,
                            updated: Optional[datetime.datetime] = None, active: bool = True,
                            page: Optional[int] = 0, page_size: Optional[int] = 1000) -> List[DataDict]:
    """
    List subscriptions with optional filters.

    :param session: The active database session.
    :type session: AlchemySession
    :param user_id: Filter by the subscription's user id.
    :type user_id: Optional[str]
    :param updated: Filter subscriptions updated on or after this datetime.
    :type updated: Optional[datetime.datetime]
    :param active: Filter by the subscription's "active" state. If set to 'True', fetches only subscriptions with the
    state 'active'. If 'False', fetch subscriptions that are not 'active'. Defaults to 'True'.
    :type active: bool
    :param page: The page number for pagination. Defaults to 0 (first page)
    :type page: Optional[int]
    :param page_size: The number of subscriptions per page, defaults to 1000 if not provided.
    :type page_size: Optional[int]
    :return: A list of subscription dictionaries.
    :rtype: List[DataDict]
    """

    query = session.query(HDXNotificationsSubscription).filter(
        HDXNotificationsSubscription.state == State.ACTIVE.value
        if active else HDXNotificationsSubscription.state != State.ACTIVE.value
    )

    if user_id:
        try:
            # Check if user_id is a valid UUID
            uuid.UUID(user_id)
            query = query.filter(HDXNotificationsSubscription.user_id == user_id)
        except ValueError:
            # If not a valid UUID, assume it's a username and join with User table
            query = query.join(model.User).filter(model.User.name == user_id)
    if updated:
        query = query.filter(HDXNotificationsSubscription.updated >= updated)

    # sort query by updated date descending
    query = query.order_by(HDXNotificationsSubscription.updated.desc())

    if page:
        query = query.offset((page - 1) * page_size)

    query = query.limit(page_size)
    subscriptions = query.all()
    return [notifications_subscription_dictize(subscription) for subscription in subscriptions]


def get_grouped_notification_subscriptions(session: AlchemySession, page: Optional[int] = None,
                                           page_size: Optional[int] = 1000) -> List[DataDict]:
    """
    Retrieve active notification subscriptions grouped by object and object_type with optional pagination.

    :param session: The active database session.
    :type session: AlchemySession
    :param page: The page number for pagination. If None, pagination is not applied.
    :type page: Optional[int]
    :param page_size: The number of subscriptions per page. Defaults to 1000 if not provided.
    :type page_size: Optional[int]
    :return: A list of grouped subscription data
    :rtype: List[DataDict]
    """

    query = (
        session.query(
            HDXNotificationsSubscription.object.label('object'),
            HDXNotificationsSubscription.object_type.label('object_type'),
            func.jsonb_agg(
                func.jsonb_build_object(
                    'user_id', HDXNotificationsSubscription.user_id,
                    'subscription_id', HDXNotificationsSubscription.id,
                    'event_type', HDXNotificationsSubscription.event_type
                )
            ).label('user_list')
        )
        .filter(HDXNotificationsSubscription.state == State.ACTIVE.value)
        .group_by(HDXNotificationsSubscription.object, HDXNotificationsSubscription.object_type)
    )

    if page:
        query = query.offset((page - 1) * page_size)

    query = query.order_by(func.max(HDXNotificationsSubscription.updated).desc())

    query = query.limit(page_size)

    return [
        {
            'object': row.object,
            'object_type': row.object_type,
            'user_list': row.user_list,
        }
        for row in query.all()
    ]

def mark_as_deleted(session: AlchemySession, subscription_id: str, commit_tx: bool) -> bool:
    """
    Mark a notification subscription as deleted by changing its state to 'deleted'.

    :param session: The active database session.
    :type session: AlchemySession
    :param subscription_id: The ID of the subscription to delete.
    :type subscription_id: str
    :param commit_tx: Whether to commit the transaction after deletion.
    :type commit_tx: bool
    :return: True if the subscription was deleted, False otherwise.
    :rtype: bool
    """
    subscription = session.query(HDXNotificationsSubscription).get(subscription_id)
    if not subscription:
        return False

    subscription.state = State.DELETED.value
    if commit_tx:
        session.commit()
    return True

def get(session: AlchemySession, id: str) -> Optional[HDXNotificationsSubscription]:
    """
    Get a notification subscription by its ID.

    :param session:
    :type session: AlchemySession
    :param id: The ID of the subscription to retrieve.
    :type id: str
    :return: The subscription object if found, None otherwise.
    :rtype: Optional[HDXNotificationsSubscription]
    """
    return session.query(HDXNotificationsSubscription).get(id)

def get_by_unsubscribe_token(unsubscribe_token_id: str) -> Optional[HDXNotificationsSubscription]:
    """
    Get a notification subscription by its unsubscribe token ID.

    :param unsubscribe_token_id: The ID of the unsubscribe token.
    :return: The subscription object if found, None otherwise.
    """
    return meta.Session.query(HDXNotificationsSubscription).filter(
        HDXNotificationsSubscription.unsubscribe_token_id == unsubscribe_token_id
    ).first()
