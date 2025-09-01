import json
import logging

from sqlalchemy import case
import ckan.model as core_model
import ckan.plugins.toolkit as tk
import ckanext.hdx_users.model as user_model
import ckan.lib.dictization.model_dictize as model_dictize
from ckan.types import Context, DataDict
from ckanext.hdx_users.controller_logic import notification_platform_logic
from ckanext.hdx_users.general_token_model import ObjectType
from ckanext.hdx_users.helpers import novu_interaction

from ckanext.hdx_users.helpers.reset_password import make_key
from ckanext.hdx_users.helpers.helpers import generate_password, generate_username, NotAuthorized
from ckanext.hdx_users.logic.schema import onboarding_default_user_schema
from ckanext.hdx_users.notifications_subscription_model import EventType, HDXNotificationsSubscription, \
    generate_notifications_subscription, notifications_subscription_dictize, State
from ckanext.security.schema import default_update_user_schema

_get_or_bust = tk.get_or_bust
ValidationError = tk.ValidationError
_check_access = tk.check_access
NotFound = tk.ObjectNotFound
get_action = tk.get_action
OnbUserNotFound = json.dumps({'success': False, 'error': {'message': 'User not found'}})
OnbSuccess = json.dumps({'success': True})

log = logging.getLogger(__name__)
USER_STATE_SHADOW = 'shadow'

def token_create(context, user):
    _check_access('user_create', context, None)
    model = context['model']
    key = make_key()
    token_obj = user_model.ValidationToken(user_id=user['id'], token=key, valid=False)
    model.Session.add(token_obj)
    model.Session.commit()
    return token_obj.as_dict()


def error_message(error_summary):
    return json.dumps({'success': False, 'error': {'message': error_summary}})


@tk.chained_action
def user_create(up_func, context, data_dict):
    """
    Perform user_create with a modified default schema.

    This function overrides the default schema used for creating new users with a modified schema. By default,
    it uses the schema specified by the 'onboarding_default_user_schema' function. If a schema is already provided
    in the context, it will use that instead.
    """
    context['schema'] = context.get('schema') or onboarding_default_user_schema()

    result = up_func(context, data_dict)
    return result

def hdx_shadow_user_create(context: Context, data_dict: DataDict) -> DataDict:
    _check_access('hdx_shadow_user_create', context, None)

    email = _get_or_bust(data_dict, 'email')
    email = email.lower()

    # Define a priority order for user states: ACTIVE → SHADOW → DELETED → PENDING → others
    state_order = case(
        (core_model.User.state == core_model.State.ACTIVE, 1),
        (core_model.User.state == USER_STATE_SHADOW, 2),
        (core_model.User.state == core_model.State.DELETED, 3),
        (core_model.User.state == core_model.State.PENDING, 4),
        else_=5
    )

    q = core_model.Session.query(core_model.User)
    q = q.filter(core_model.User.email == email)
    q = q.order_by(state_order, core_model.User.created.desc())
    user_obj = q.first()

    user_dictize_context = context.copy()

    if user_obj:
        if user_obj.state == core_model.State.ACTIVE or user_obj.state == USER_STATE_SHADOW:
            user_dict = model_dictize.user_dictize(user_obj, user_dictize_context, include_plugin_extras=False)
            user_dict['action_performed'] = 'none'
            return user_dict
        if user_obj.state == core_model.State.PENDING:
            context['schema'] = default_update_user_schema()
            user_dict = get_action('user_patch')(
                context,
                {
                    'id': user_obj.id,
                    'state': USER_STATE_SHADOW,
                },
            )
            user_dict['action_performed'] = 'from-pending-to-shadow'
            return user_dict

    if not user_obj or user_obj.state == core_model.State.DELETED:
        context['schema'] = onboarding_default_user_schema()
        data_dict['state'] = USER_STATE_SHADOW
        data_dict['password'] = data_dict['password1'] = generate_password(32)
        data_dict['name'] = generate_username(12, 24)
        data_dict['fullname'] = data_dict['name'].replace('-', '').replace('_', '')

        try:
            user_dict = get_action('user_create')(context, data_dict)
            user_dict['action_performed'] = 'created-shadow-account'
        except Exception:
            raise NotAuthorized
        return user_dict

    raise NotFound

def hdx_notifications_subscription_create(context: Context, data_dict: DataDict) -> DataDict:
    """
    Creates a notification subscription for a user to receive notifications based on
    specified object and event types.

    Regular users can only create subscriptions for themselves
    Sysadmins can create subscriptions for any user by specifying a user_id
    :param context:
    :type context: Context
    :param data_dict:
    :type data_dict: DataDict

    Required keys in data_dict:
        - object_type: Type of entity to subscribe to (dataset, group, organization, crisis)
        - object: ID of the entity
        - event_type: Type of event to subscribe to (new-dataset-added, dataset-updated)

    Optional keys in data_dict:
        - user_id: ID of user that we want to create the subscription for (sysadmins only)
        - query_params: Additional parameters for general-search subscriptions (as dict)

    :returns: the created subscription
    :rtype: DataDict
    """

    log.info('Creating new subscription for user %s', data_dict.get('user_id'))
    _check_access('hdx_notifications_subscription_create', context, data_dict)
    tk.get_or_bust(data_dict, ['object_type', 'object', 'event_type'])

    user_id = data_dict.get('user_id') or context.get('user')

    session = context['session']

    if data_dict.get('object_type') == 'general-search':
        query_params = data_dict.get('query_params')
        if isinstance(query_params, dict):
            data_dict['query_params'] = query_params
        else:
            log.warning('Expected a dictionary for query_params')
            data_dict['query_params'] = None

    try:
        object_type = ObjectType(data_dict['object_type'])
    except ValueError:
        raise tk.ValidationError(f'Invalid object_type: {data_dict["object_type"]}')

    action = None
    if object_type == ObjectType.DATASET:
        action = 'package_show'
    elif object_type == ObjectType.GROUP:
        action = 'group_show'
    elif object_type == ObjectType.ORGANIZATION:
        action = 'organization_show'
    elif object_type == ObjectType.CRISIS:
        action = 'page_show'
    else:
        raise tk.ValidationError(f'Invalid object_type: {data_dict["object_type"]}')

    try:
        object_obj = get_action(action)({}, {'id': data_dict['object']})
        user_dict = get_action('user_show')(context, {'id': user_id})
        user_email = data_dict.get('email') or user_dict.get('email')
    except tk.ObjectNotFound:
        raise tk.ValidationError(f'{object_type} {data_dict["object"]} does not exist')
    except Exception as e:
        log.error(f'Error retrieving object or user: {e}')
        raise e

    try:
        event_type_enum = EventType(data_dict['event_type'])
    except ValueError:
        raise tk.ValidationError(f'Invalid event_type: {data_dict["event_type"]}')

    # Check that the same subscription does not already exist
    existing_subscription = session.query(HDXNotificationsSubscription).filter(
        HDXNotificationsSubscription.user_id == user_dict['id'],
        HDXNotificationsSubscription.object_type == object_type,
        HDXNotificationsSubscription.object == data_dict['object'],
        HDXNotificationsSubscription.event_type == event_type_enum,
        HDXNotificationsSubscription.state == State.ACTIVE.value
    ).first()

    if existing_subscription:
        log.warning(f'Subscription already exists for user {user_dict["name"]} '
                        f'on {object_type.value} {data_dict["object"]}')
        raise tk.ValidationError(f'Subscription already exists '
                        f'on this {object_type.display_name}')

    # create unsubscribe token if it does not exist
    unsubscribe_token_obj = notification_platform_logic.get_or_generate_unsubscribe_token(
        session,
        user_dict['id'],
        object_type,
        object_obj['id'],
        commit_tx=False
    )

    # create the subscription in HDX database
    subscription = generate_notifications_subscription(
        session=session,
        user_id=user_dict['id'],
        object_type=object_type,
        object=object_obj['id'],
        event_type=event_type_enum,
        unsubscribe_token_id=unsubscribe_token_obj.id,
        query_params=data_dict.get('query_params'),
        commit_tx=False
    )


    novu_interaction.add_subscription_info(
        user_dict['id'], user_email, unsubscribe_token_obj, object_type, object_obj['id'], object_obj
    )

    session.commit()
    subscription_dict = notifications_subscription_dictize(subscription)
    subscription_dict['unsubscribe_token'] = unsubscribe_token_obj.token
    return subscription_dict
