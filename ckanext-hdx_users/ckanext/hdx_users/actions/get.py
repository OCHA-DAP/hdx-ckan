import logging
import pylons.config as config
from ckan.plugins import toolkit as tk
import ckan.model as model

import ckan.logic as logic
import ckan.logic.action.get as user_get
import ckan.lib.dictization.model_dictize as model_dictize
import ckanext.hdx_users.model as user_model

log = logging.getLogger(__name__)
_check_access = logic.check_access
NotFound = logic.NotFound
get_action = logic.get_action
NoOfLocs = 5
NoOfOrgs = 5
c_nepal_earthquake = config.get('hdx.crisis.nepal_earthquake')


@logic.side_effect_free
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

    query = model.User.search(q).order_by(None)
    query = query.filter(model.User.state == model.State.ACTIVE)
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


# moved from misc.py
def hdx_user_show(context, data_dict):
    '''Return a user account.

    Either the ``id`` or the ``user_obj`` parameter must be given.

    :param id: the id or name of the user (optional)
    :type id: string
    :param user_obj: the user dictionary of the user (optional)
    :type user_obj: user dictionary

    :rtype: dictionary

    '''
    model = context['model']

    id = data_dict.get('id', None)
    provided_user = data_dict.get('user_obj', None)
    if id:
        user_obj = model.User.get(id)
        context['user_obj'] = user_obj
        if user_obj is None:
            raise logic.NotFound
    elif provided_user:
        context['user_obj'] = user_obj = provided_user
    else:
        raise logic.NotFound

    _check_access('user_show', context, data_dict)

    user_dict = model_dictize.user_dictize(user_obj, context)

    if context.get('return_minimal'):
        return user_dict

    revisions_q = model.Session.query(model.Revision
                                      ).filter_by(author=user_obj.name)

    revisions_list = []
    for revision in revisions_q.limit(20).all():
        revision_dict = tk.get_action('revision_show')(context, {'id': revision.id})
        revision_dict['state'] = revision.state
        revisions_list.append(revision_dict)
    user_dict['activity'] = revisions_list

    offset = data_dict.get('offset', 0)
    limit = data_dict.get('limit', 20)
    print data_dict.get('sort', None)
    sort = data_dict.get('sort', 'metadata_modified desc')
    user_dict['datasets'] = []
    dataset_q = model.Session.query(model.Package).join(model.PackageRole).filter_by(user=user_obj,
                                                                                     role=model.Role.ADMIN
                                                                                     ).order_by(sort).offset(
        offset).limit(limit)

    dataset_q_counter = model.Session.query(model.Package).join(model.PackageRole
                                                                ).filter_by(user=user_obj, role=model.Role.ADMIN
                                                                            ).count()

    for dataset in dataset_q:
        try:
            dataset_dict = tk.get_action('package_show')(context, {'id': dataset.id})
        except tk.NotAuthorized:
            continue
        user_dict['datasets'].append(dataset_dict)

    user_dict['num_followers'] = tk.get_action('user_follower_count')(
        {'model': model, 'session': model.Session},
        {'id': user_dict['id']})
    user_dict['total_count'] = dataset_q_counter
    return user_dict


@logic.side_effect_free
def hdx_user_fullname_show(context, data_dict):
    if 'id' not in data_dict:
        raise NotFound("Id not provided")

    _check_access('user_show', context, data_dict)

    user_id = data_dict.get('id')
    user_dict = {'id': user_id}
    # if 'include_user_dict' in data_dict and data_dict.get('include_user_dict') == 'true':
    # try:
    #     user_dict = get_action('user_show')(context, {'id': user_id})
    # except Exception, ex:
    #     log.error(ex)
    #     raise NotFound("user not found")
    # user_obj = model.User.get(user_id)
    _set_user_names(context, user_dict)
    return user_dict


def _set_user_names(context, user_dict):
    if user_dict and 'id' in user_dict:
        try:
            first_name = get_action('user_extra_value_by_key_show')(context,
                                                                    {'user_id': user_dict.get('id'),
                                                                     'key': user_model.HDX_FIRST_NAME})
            user_dict['firstname'] = first_name.get(user_model.HDX_FIRST_NAME)
        except Exception, ex:
            user_dict['firstname'] = None
        try:
            last_name = get_action('user_extra_value_by_key_show')(context,
                                                                   {'user_id': user_dict.get('id'),
                                                                    'key': user_model.HDX_LAST_NAME})
            user_dict['lastname'] = last_name.get(user_model.HDX_LAST_NAME)
        except  Exception, ex:
            user_dict['lastname'] = None
    return user_dict


@logic.side_effect_free
def user_show(context, data_dict):
    user_dict = user_get.user_show(context, data_dict)
    if user_dict:
        _set_user_names(context, user_dict)
    return user_dict
