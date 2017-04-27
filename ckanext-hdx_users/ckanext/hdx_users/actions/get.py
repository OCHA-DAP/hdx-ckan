import ckanext.hdx_users.model as umodel
import ckan.logic as logic
import pylons.config as config

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
        if is_custom(item.get('extras', {})):
            if item['name'] == c_nepal_earthquake:
                type = 'crisis'
            result.append(create_item(item, type, False))
        else:
            if i <= NoOfLocs:
                result_aux.append(create_item(item, type, False))
                i += 1

    orgs = get_action('cached_organization_list')(context, {})
    orgs = sorted(orgs, key=lambda elem: elem.get('package_count', 0), reverse=True)

    i = 1
    type = 'organization'
    for item in orgs:
        if is_custom(item['extras']):
            result.append(create_item(item, type, False))
        else:
            if i <= NoOfOrgs:
                result_aux.append(create_item(item, type, False))
                i += 1

    result.extend(result_aux)
    return result


def is_custom(extras):
    for item in extras:
        if 'key' in item and ('custom_loc' == item['key'] or 'custom_org' == item['key']) and '1' == item['value']:
            return True
    return False


def create_item(item, type, follow=False):
    return {'id': item['id'], 'name': item['name'], 'display_name': item['display_name'], 'type': type,
            'follow': follow}
