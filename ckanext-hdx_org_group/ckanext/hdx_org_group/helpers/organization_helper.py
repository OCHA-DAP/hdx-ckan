'''
Created on Jan 14, 2015

@author: alexandru-m-g
'''
import ckan.logic as logic
get_action = logic.get_action


def sort_results_case_insensitive(results, sort_by):
    if results:
        if sort_by == 'title asc':
            return sorted(results, key=lambda x: x.get('title', '').lower())
        elif sort_by == 'title desc':
            return sorted(results, key=lambda x: x.get('title', '').lower(), reverse=True)
    return results


def hdx_get_group_activity_list(context, data_dict):
    from ckanext.hdx_package.helpers import helpers as hdx_package_helpers
    activity_stream = get_action('group_activity_list')(context, data_dict)
    offset = int(data_dict.get('offset', 0))
    extra_vars = {
        'controller': 'group',
        'action': 'activity',
        'id': data_dict['id'],
        'offset': offset,
    }
    return hdx_package_helpers._activity_list(context, activity_stream, extra_vars)
