'''
Created on Apr 11, 2014

@author: alexandru-m-g
'''

import logging
import bisect
import ckan.lib.navl.dictization_functions as df

import ckanext.hdx_package.helpers.geopreview as geopreview
import ckanext.hdx_package.helpers.caching as caching

from ckan.common import _, c

missing = df.missing
StopOnError = df.StopOnError
Invalid = df.Invalid


def groups_not_empty(key, data, errors, context):
    """
    When creating a package, groups cannot be empty
    """
    # All the extra logic here is needed to deal with the multi-step wizard used for creating a new dataset
    # We need to make sure that the validation only runs at the last step of the wizard

    # allow_partial_update = context.get('allow_partial_update', False)
    # allow_state_change = context.get('allow_state_change', False)
    first_phase = False

    for data_key, data_value in data.items():
        if data_key[0] == '__extras':
            wizard_phase = data_value.get('_ckan_phase', 'Other')
            if wizard_phase == 'dataset_new_1':
                first_phase = True
                break

    group_list = caching.cached_group_list()
    country_names = [group['name'] for group in group_list if group.get('name')]
    country_ids = [group['id'] for group in group_list]
    country_names.sort()
    country_ids.sort()

    if not first_phase:
        error_msg = _('Missing value')
        problem_appeared = False
        try:
            num_of_groups = max((key[1] for key in data.keys() if key[0] == 'groups')) + 1
        except ValueError, e:
            num_of_groups = 0
            problem_appeared = True

        for group_idx in range(0, num_of_groups):
            group_correct = False
            group_id = data.get(('groups', group_idx, 'id'))
            if group_id and _in_sorted_list(group_id, country_ids):
                group_correct = True
            else:
                group_name = data.get(('groups', group_idx, 'name'))
                if group_name and _in_sorted_list(group_name, country_names):
                    group_correct = True

            if not group_correct:
                error_msg = _('Wrong country code or id')
                problem_appeared = True
                break

        if problem_appeared:
            errors[key].append(error_msg)
            raise StopOnError
    return None


def _in_sorted_list(value, sorted_list):
    index = bisect.bisect_left(sorted_list, value)
    if index != len(sorted_list) and sorted_list[index] == value:
        return True
    return False


def detect_format(key, data, errors, context):
    '''
    resource url should not be empty
    '''

    current_format = data.get(key)
    if not current_format:
        url = data.get((key[0], key[1], 'url'))
        file_format = geopreview.detect_format_from_extension(url)
        if file_format:
            data[key] = file_format
            return file_format
        raise df.Invalid(_('No format provided and none could be automatically deduced'))

    return current_format


def find_package_creator(key, data, errors, context):
    current_creator = data.get(key)
    if not current_creator:
        user = c.user or c.author
        if user:
            data[key] = user
            current_creator = user

    return current_creator