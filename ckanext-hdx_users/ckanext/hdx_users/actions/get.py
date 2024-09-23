import logging

import ckan.logic as logic
import ckan.logic.action.get as user_get
import ckan.plugins.toolkit as tk
import ckanext.hdx_users.model as user_model
from ckan.types import ActionResult, Context, DataDict

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
        default: 20)
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

    query = model.User.search(q).order_by(None)
    query = query.filter(model.User.state == model.State.ACTIVE)
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

    user_list = []
    for user in query.all():
        result_dict = {}
        for k in ['id', 'name', 'fullname']:
            result_dict[k] = getattr(user, k)
        user_list.append(result_dict)

    return user_list
