import logging

import ckan.logic as logic
import ckan.logic.action.get as user_get
import ckan.plugins.toolkit as tk
import ckanext.hdx_users.model as user_model

config = tk.config
log = logging.getLogger(__name__)
_check_access = tk.check_access
NotFound = tk.ObjectNotFound
get_action = tk.get_action
NoOfLocs = 5
NoOfOrgs = 5
c_nepal_earthquake = config.get('hdx.crisis.nepal_earthquake')


@tk.side_effect_free
def onboarding_followee_list(context, data_dict):
    # TODO check if user is following org&locs
    result = []

    # data_filter = {'package_count': True, 'include_extras': True, 'all_fields': True, 'sort': 'package_count desc'}

    locs = get_action('cached_group_list')(context, {})
    locs = sorted(locs, key=lambda elem: elem.get('package_count', 0), reverse=True)

    result_aux = []
    i = 1
    for item in locs:
        type = 'location'
        if item.get('activity_level') == 'active':
            if item['name'] == c_nepal_earthquake:
                type = 'crisis'
            result.append(create_item(item, type, False))
        else:
            if i <= NoOfLocs:
                result_aux.append(create_item(item, type, False))
                i += 1

    orgs = get_action('cached_organization_list')({}, {})
    orgs = sorted(orgs, key=lambda elem: elem.get('package_count', 0), reverse=True)

    i = 1
    type = 'organization'
    for item in orgs:
        if item.get('custom_org', '0') == '1':
            result.append(create_item(item, type, False))
        else:
            if i <= NoOfOrgs:
                result_aux.append(create_item(item, type, False))
                i += 1

    result.extend(result_aux)
    return result


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

    user_list = []
    for user in query3.all():
        result_dict = {}
        for k in ['id', 'name', 'fullname']:
            result_dict[k] = getattr(user, k)

        user_list.append(result_dict)

    return user_list


@tk.side_effect_free
def hdx_user_fullname_show(context, data_dict):
    if 'id' not in data_dict:
        raise NotFound("Id not provided")

    _check_access('user_show', context, data_dict)

    user_id = data_dict.get('id')
    user_dict = {'id': user_id}
    _set_user_names(context, user_dict)
    return user_dict


def _set_user_names(context, user_dict):
    if user_dict and 'id' in user_dict:
        try:
            first_name = get_action('user_extra_value_by_key_show')(context,
                                                                    {'user_id': user_dict.get('id'),
                                                                     'key': user_model.HDX_FIRST_NAME})
            user_dict['firstname'] = first_name.get(user_model.HDX_FIRST_NAME)
        except Exception as ex:
            user_dict['firstname'] = None
        try:
            last_name = get_action('user_extra_value_by_key_show')(context,
                                                                   {'user_id': user_dict.get('id'),
                                                                    'key': user_model.HDX_LAST_NAME})
            user_dict['lastname'] = last_name.get(user_model.HDX_LAST_NAME)
        except Exception as ex:
            user_dict['lastname'] = None
    return user_dict


@tk.side_effect_free
def user_show(context, data_dict):
    user_dict = user_get.user_show(context, data_dict)
    if user_dict:
        _set_user_names(context, user_dict)
    return user_dict
