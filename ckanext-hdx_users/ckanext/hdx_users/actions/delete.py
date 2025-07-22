import json
import logging

import ckan.plugins.toolkit as tk
import ckanext.hdx_theme.helpers.helpers as theme_h

from ckan.types import DataDict, Context
from ckanext.hdx_users.helpers import novu_interaction
from ckanext.hdx_users.general_token_model import get_by_token_with_checks, validate_token, TokenType, ObjectType
from ckanext.hdx_users.notifications_subscription_model import (mark_as_deleted,
                                                                get_by_unsubscribe_token)

_get_or_bust = tk.get_or_bust
ValidationError = tk.ValidationError
_check_access = tk.check_access
NotFound = tk.ObjectNotFound
NotAuthorized = tk.NotAuthorized
get_action = tk.get_action
chained_action = tk.chained_action
OnbUserNotFound = json.dumps({'success': False, 'error': {'message': 'User not found'}})
OnbSuccess = json.dumps({'success': True})


log = logging.getLogger(__name__)


@chained_action
def hdx_user_delete(original_action, context, data_dict):
    '''Delete a user. If user is maintainer for a datasets, it returns error
    copied&adapted from ckan/logic/action/delete.py:L36

    Only sysadmins can delete users.

    :param id: the id or username of the user to delete
    :type id: string
    '''

    _check_access('user_delete', context, data_dict)

    model = context['model']
    user_username = _get_or_bust(data_dict, 'id')
    user_obj = model.User.get(user_username)
    if user_obj:
        user_id = user_obj.id
        if user_id:
            org_list = get_action('organization_list_for_user')(context, {'id': user_id})
            if org_list:
                for org in org_list:
                    pkg_list_for_maintainer = theme_h._get_packages_for_maintainer(context, user_id, org.get('name'))
                    if pkg_list_for_maintainer and len(pkg_list_for_maintainer) > 0:
                        raise NotAuthorized('User can not be deleted as it is maintainer for datasets')

    return original_action(context, data_dict)


def hdx_notifications_subscription_delete(context: Context, data_dict: DataDict) -> DataDict:
    """
    Deletes a notification subscription for a user by its ID.

    Regular users can only delete subscriptions for themselves
    Sysadmins can delete subscriptions for any user

    """
    session = context['session']
    log.info('Deleting subscription for user %s', data_dict.get('user_id'))

    token = tk.get_or_bust(data_dict, 'token')
    token_obj = get_by_token_with_checks(token, TokenType.UNSUBSCRIBE_FOR_NOTIFICATION)
    subscription = get_by_unsubscribe_token(token_obj.id)
    if not subscription:
        raise NotFound(f'Subscription with token {token} not found')
    subscription_id = subscription.id
    _check_access('hdx_notifications_subscription_delete', context, {'id': subscription_id})

    mark_as_deleted(session, subscription_id, commit_tx=False)
    validate_token(session, token, TokenType.UNSUBSCRIBE_FOR_NOTIFICATION, commit_tx=False)

    object_type = ObjectType(subscription.object_type)
    novu_interaction.remove_subscription_info(token_obj.user_id, subscription.object, object_type)

    session.commit()

    return {'message': f'Subscription {subscription_id} deleted successfully'}
