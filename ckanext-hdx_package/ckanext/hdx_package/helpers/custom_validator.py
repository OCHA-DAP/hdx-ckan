'''
Created on Apr 11, 2014

@author: alexandru-m-g
'''

import bisect
import re

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

_DATASET_PREVIEW_FIRST_RESOURCE = 'first_resource'
_DATASET_PREVIEW_RESOURCE_ID = 'resource_id'
_DATASET_PREVIEW_NO_PREVIEW = 'no_preview'
DATASET_PREVIEW_VALUES_LIST = [_DATASET_PREVIEW_FIRST_RESOURCE, _DATASET_PREVIEW_RESOURCE_ID,
                               _DATASET_PREVIEW_NO_PREVIEW]

# Regular expression for validating urls based on
# https://stackoverflow.com/questions/7160737/python-how-to-validate-a-url-in-python-malformed-or-not
# from Django framework

url_regex = re.compile(
        r'^(?:http|ftp)s?://' # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
        r'localhost|' #localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
        r'(?::\d+)?' # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)


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


def hdx_is_url(key, data, errors, context):
    value = data.get(key)
    match_result = re.match(url_regex, value)
    if match_result is None:
        errors[key].append(_('Value is not a URL'))
        raise StopOnError


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


def hdx_dataset_preview_validator(key, data, errors, context):
    try:
        dataset_preview = str(data.get(key))
        if dataset_preview and dataset_preview in DATASET_PREVIEW_VALUES_LIST:
            return data[key]
        data[key] = _DATASET_PREVIEW_FIRST_RESOURCE
    except Exception, ex:
        data[key] = _DATASET_PREVIEW_FIRST_RESOURCE
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


def hdx_convert_to_timestamp(key, data, errors, context):
    '''
    value set to true will be changed to timestamp, otherwise none
    '''

    # value = data.get(key)
    # if value and value in ('1', 1):
    #     data[key] = datetime.datetime.utcnow().isoformat()
    # elif value and value in ('0', 0):
    #     data[key] = None
    # # else:
    # #     data[key] = None
    # return data[key]

    value = data.get(key)
    if value in (True, False, 'True', 'False'):
        pass
    elif value in ('1', 1):
        # set others on False
        i = 0
        while True:
            temp_key_name = ('resources', i, 'name')
            temp_key_preview = ('resources', i, 'dataset_preview_enabled')
            if not data.get(temp_key_name):
                break
            data[temp_key_preview] = False
            i += 1
        data[key] = True

    elif value in ('0', 0):
        data[key] = False
    else:
        # value not in ('1',1,'0',0, True, False, 'True', 'False'):
        data[key] = None
    return data[key]


def hdx_convert_list_item_to_extras(key, data, errors, context):
    # Get the current extras index
    current_indexes = [k[1] for k in data.keys()
                       if len(k) > 1 and k[0] == 'extras']

    new_index = max(current_indexes) + 1 if current_indexes else 0

    data[('extras', new_index, 'key')] = '__'.join((str(item) for item in key))
    data[('extras', new_index, 'value')] = data[key]


def hdx_convert_from_extras_to_list_item(key, data, errors, context):
    def remove_from_extras(data, key):
        to_remove = []
        for data_key, data_value in data.iteritems():
            if (data_key[0] == 'extras'
                and data_key[1] == key):
                to_remove.append(data_key)
        for item in to_remove:
            del data[item]

    keys_to_remove = []
    key_value_to_add = []

    for data_key, data_value in data.iteritems():
        if isinstance(data_value, basestring):
            data_value_parts = data_value.split('__') # Example: ['customviz', 0, 'url']
            key_parts = key[-1].split('__') # Example ['customviz', 'url']
            if data_key[0] == 'extras' and data_key[-1] == 'key' \
                    and len(data_value_parts) == 3 and len(key_parts) == 2 \
                    and data_value_parts[0] == key_parts[0] and data_value_parts[2] == key_parts[1]:

                list_name = key_parts[0]
                property_name = key_parts[1]

                # current_indexes = [k[1] for k in data.keys()
                #                    if len(k) == 3 and k[0] == list_name and k[2] == property_name]
                # index = max(current_indexes) + 1 if current_indexes else 0

                key_value_to_add.append({
                    'key': (list_name, data_key[1], property_name),
                    'value': data[('extras', data_key[1], 'value')]
                })
                keys_to_remove.append(data_key[1])

    for key_val in key_value_to_add:
        data[key_val['key']] = key_val['value']

    for k in keys_to_remove:
        remove_from_extras(data, k)


def hdx_boolean_string_converter(value, context):
    '''
    Return a boolean for value.
    Return value when value is a python bool type.
    Return True for strings 'true', 'yes', 't', 'y', and '1'.
    Return False in all other cases, including when value is an empty string or
    None
    '''
    if value is missing or value is None:
        return "false"
    if isinstance(value, bool):
        return "true" if value else "false"
    if value.lower() in ['true', 'yes', 't', 'y', '1']:
        return "true"
    return "false"
