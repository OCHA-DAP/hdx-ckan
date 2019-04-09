import ckan.plugins.toolkit as tk

import ckanext.hdx_org_group.helpers.caching as caching

_check_access = tk.check_access


def invalidate_data_completeness_for_location(context, data_dict):
    _check_access('invalidate_data_completeness_for_location', context, data_dict)
    location_code = data_dict.get('name')
    message = 'Couldn\'t invalidate data completeness for ' + location_code
    if location_code:
        caching.cached_data_completeness.invalidate(location_code)
        message = 'Successfully invalidated data completeness cache for ' + location_code

    return {
        'message': message
    }
