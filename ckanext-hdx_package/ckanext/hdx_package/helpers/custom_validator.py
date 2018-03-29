'''
Created on Apr 11, 2014

@author: alexandru-m-g
'''

import bisect

import ckanext.hdx_package.helpers.caching as caching
import ckanext.hdx_package.helpers.geopreview as geopreview
import ckan.logic as logic
import ckan.model as model

import ckan.lib.navl.dictization_functions as df
from ckan.common import _, c

missing = df.missing
StopOnError = df.StopOnError
Invalid = df.Invalid
get_action = logic.get_action

_DATA_PREVIEW_FIRST_RESOURCE = 'first_resource'
_DATA_PREVIEW_RESOURCE_ID = 'resource_id'
_DATA_PREVIEW_NO_PREVIEW = 'no_preview'
DATA_PREVIEW_VALUES_LIST = [_DATA_PREVIEW_FIRST_RESOURCE, _DATA_PREVIEW_RESOURCE_ID, _DATA_PREVIEW_NO_PREVIEW]


# same as not_empty, but ignore whitespaces
def not_empty_ignore_ws(key, data, errors, context):
    value = data.get(key)
    if not value or value is missing:
        errors[key].append(_('Missing value'))
        raise StopOnError
    value = value.strip()
    if not value or value is missing:
        errors[key].append(_('Missing value'))
        raise StopOnError


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
    if not current_format or isinstance(current_format, df.Missing):
        url = data.get((key[0], key[1], 'url'))
        file_format = geopreview.detect_format_from_extension(url)
        if not file_format:
            name = data.get((key[0], key[1], 'name'))
            file_format = geopreview.detect_format_from_extension(name)
        if file_format:
            data[key] = file_format
            return file_format
        raise df.Invalid(_('No format provided and none could be automatically deduced'))

    return current_format


def hdx_show_subnational(key, data, errors, context):
    '''
    resource url should not be empty
    '''

    current_value = data.get(key)
    if not current_value or isinstance(current_value, df.Missing):
        data[key] = "0"
        return data[key]
    if current_value in ["true", "True", "1"]:
        data[key] = "1"
        return data[key]
    if current_value in ["false", "False", "0", None]:
        data[key] = "0"
        return data[key]

    data[key] = "0"
    return data[key]


def find_package_creator(key, data, errors, context):
    current_creator = data.get(key)
    if not current_creator:
        user = c.user or c.author
        if user:
            data[key] = user
            current_creator = user

    return current_creator


def hdx_find_package_maintainer(key, data, errors, context):
    try:
        user_obj = model.User.get(data.get(key))
    except Exception, ex:
        raise df.Invalid(_('Maintainer does not exist. Please add valid user ID'))

    org_id = data.get(('owner_org',))
    if not org_id:
        raise df.Invalid(_('Organizations owner does not exist. Please add an organization ID'))

    members = get_action('hdx_member_list')(context, {'org_id': org_id})

    if user_obj and ((user_obj.id in members.get('all')) or user_obj.sysadmin):
        data[key] = user_obj.id
        return data[key]
    raise df.Invalid(_('Maintainer does not exist or is not a member of current owner organization.'
                       ' Please add valid user ID'))


def hdx_data_preview_validator(key, data, errors, context):
    try:
        data_preview = str(data.get(key))
        if data_preview and data_preview in DATA_PREVIEW_VALUES_LIST:
            return data[key]
        # if data_preview is None or data_preview == '' or data_preview == 'None':
        # first_resource
        data[key] = _DATA_PREVIEW_FIRST_RESOURCE
    except Exception, ex:
        data[key] = _DATA_PREVIEW_FIRST_RESOURCE
    return data[key]


def general_not_empty_if_other_selected(other_key, other_compare_value):
    '''

    :param other_key: the key of the field that influences this "_other" field. Ex. 'methodology', 'license_id'
    :type other_key: str
    :param other_compare_value: value of "other_key" field that maked this "_other" field mandatory. Ex. 'Other', 'hdx-other'
    :type other_compare_value: str
    :return: the validator function
    :rtype: not_empty_if_other_selected
    '''

    def not_empty_if_other_selected(key, data, errors, context):
        value = data.get(key)
        other_value = data.get((other_key,))
        if not value and other_value == other_compare_value:
            errors[key].append(_('Missing value'))
            raise StopOnError
        elif other_value != other_compare_value:
            del data[key]

            # Don't go further in the validation chain. Ex: convert to extras doesn't need to be called
            raise StopOnError

    return not_empty_if_other_selected
