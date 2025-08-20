import logging
import datetime
from typing import Optional, List

import ckan.logic as logic
import ckan.authz as authz
import ckan.plugins.toolkit as tk
from ckan.types import ActionResult, Context, DataDict

from ckanext.hdx_users.notifications_subscription_model import list_notifications_subscriptions, \
    get_grouped_notification_subscriptions

config = tk.config
log = logging.getLogger(__name__)
_check_access = tk.check_access
NotFound = tk.ObjectNotFound
get_action = tk.get_action
NoOfLocs = 5
NoOfOrgs = 5

def create_item(item, type, follow=False):
    return {'id': item['id'], 'name': item['name'], 'display_name': item['display_name'], 'type': type,
            'follow': follow}


@logic.validate(logic.schema.default_autocomplete_schema)
def hdx_user_autocomplete(context, data_dict):
    '''Return a list of user names that contain a string.

    :param q: the string to search for
    :type q: string
    :param limit: the maximum number of user names to return (optional,
        default: ``20``)
    :type limit: int

    :rtype: a list of user dictionaries each with keys ``'name'``,
        ``'fullname'``, and ``'id'``

    '''
    model = context['model']
    user = context['user']

    _check_access('user_autocomplete', context, data_dict)

    q = data_dict['q']
    if data_dict['__extras']:
        org = data_dict['__extras']['org']
    limit = data_dict.get('limit', 20)
    ignore_self = data_dict.get('ignore_self', False)

    query = model.User.search(q, user_name=user)
    query = query.filter(model.User.state != model.State.DELETED)

    if ignore_self:
        query = query.filter(model.User.name != user)

    if org:
        query1 = query.filter(model.User.id == model.Member.table_id) \
            .filter(model.Member.table_name == "user") \
            .filter(model.Member.group_id == model.Group.id) \
            .filter((model.Group.name == org) | (model.Group.id == org)) \
            .filter(model.Member.state == model.State.ACTIVE)

        # needed for maintainer to display the sysadmins too (#HDX-5554)
        query2 = query.filter((model.User.sysadmin == True))
        query3 = query2.union(query1)

        # query3 = union(query1,query2)

        query3 = query3.limit(limit)
        query = query3

    user_list: ActionResult.UserAutocomplete = []
    for user in query.all():
        result_dict = {}
        for k in ['id', 'name', 'fullname']:
            result_dict[k] = getattr(user, k)

        user_list.append(result_dict)

    return user_list


@tk.side_effect_free
def hdx_notifications_subscription_list(context: Context, data_dict: DataDict) -> List[DataDict]:
    """
    Return a list of notifications subscriptions.

    Non-sysadmin users will see only their own subscriptions.
    Parameters in data_dict:
      - user_id: Optional[str]
      - updated: Optional[datetime.datetime]
      - active: Optional[bool]
      - page: Optional[int]
      - page_size: Optional[int]
    """
    _check_access('hdx_notifications_subscription_list', context, data_dict)

    user: str = context['user']

    # Only sysadmins can call without a user_id; non-sysadmins will override with their user id.
    user_id_param = data_dict.get('user_id')
    if not authz.is_sysadmin(user):
        user_id_param = user

    updated_str = data_dict.get('updated')
    updated = datetime.datetime.fromisoformat(updated_str) if updated_str else None
    active: Optional[bool] = data_dict.get('active', 'True') == 'True'
    page: Optional[int] = int(data_dict.get('page', 0) or 0)
    page_size: int = int(data_dict.get('page_size', 1000))

    session = context['session']
    return list_notifications_subscriptions(
        session,
        user_id=user_id_param,
        updated=updated,
        active=active,
        page=page,
        page_size=page_size
    )


@tk.side_effect_free
def hdx_notifications_grouped_subscription_list(context: Context, data_dict: DataDict) -> List[DataDict]:
    """
    Return a list of active subscriptions grouped by object and object_type.

    Each group includes a list of users subscribed to that object, along with
    their subscription ID and event type.

    Only accessible to sysadmins.
    """
    _check_access('hdx_notifications_grouped_subscription_list', context, data_dict)

    session = context['session']
    page: Optional[int] = int(data_dict.get('page', 0) or 0)
    page_size: int = int(data_dict.get('page_size', 1000))

    return get_grouped_notification_subscriptions(session, page=page, page_size=page_size)
