import ckanext.hdx_users.model as umodel
import ckan.logic as logic
import pylons.config as config

NotFound = logic.NotFound
get_action = logic.get_action
NoOfLocs = 5
NoOfOrgs = 5
c_nepal_earthquake = config.get('hdx.crisis.nepal_earthquake')


def token_show(context, user):
    model = context['model']
    id = user.get('id')
    token_obj = umodel.ValidationToken.get(user_id=id)
    if token_obj is None:
        raise NotFound
    return token_obj.as_dict()


def token_show_by_id(context, data_dict):
    # model = context['model']
    id = data_dict['id']
    token_obj = umodel.ValidationToken.get_by_token(token=id)
    if token_obj is None:
        raise NotFound
    return token_obj.as_dict()


@logic.side_effect_free
def onboarding_followee_list(context, data_dict):
    # model = context['model']
    # TODO check if user is following org&locs
    result = []

    locs = get_action('group_list')(context, {'package_count': True, 'include_extras': True, 'all_fields': True,
                                              'sort': 'package_count desc'})
    result_aux = []
    i = 1
    for item in locs:
        type = 'location'
        if is_custom(item['extras']):
            if item['name'] == c_nepal_earthquake:
                type = 'crisis'
            result.append({'id': item['id'], 'name': item['name'], 'display_name': item['display_name'], 'type': type,
                           'follow': False})
        else:
            if i <= NoOfLocs:
                result_aux.append(
                    {'id': item['id'], 'name': item['name'], 'display_name': item['display_name'], 'type': type,
                     'follow': False})
                i += 1

    orgs = get_action('organization_list')(context, {'package_count': True, 'include_extras': True, 'all_fields': True,
                                                     'sort': 'package_count desc'})
    i = 1
    type = 'organization'
    for item in orgs:
        if is_custom(item['extras']):
            result.append({'id': item['id'], 'name': item['name'], 'display_name': item['display_name'], 'type': type,
                           'follow': False})
        else:
            if i <= NoOfOrgs:
                result_aux.append(
                    {'id': item['id'], 'name': item['name'], 'display_name': item['display_name'], 'type': type,
                     'follow': False})
                i += 1

    result.extend(result_aux)
    return result


def is_custom(extras):
    for item in extras:
        if 'key' in item and ('custom_loc' == item['key'] or 'custom_org' == item['key']) and '1' == item['value']:
            return True
    return False
