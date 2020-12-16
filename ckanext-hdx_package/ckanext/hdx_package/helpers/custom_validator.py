'''
Created on Apr 11, 2014

@author: alexandru-m-g
'''

import bisect
import re
import datetime
import logging
import json

import ckan.model as model
import ckan.authz as authz
import ckan.plugins.toolkit as tk
import ckan.lib.navl.dictization_functions as df
from ckan.common import _, c

import ckanext.hdx_package.helpers.caching as caching
import ckanext.hdx_package.helpers.geopreview as geopreview

from ckanext.hdx_package.helpers.constants import FILE_WAS_UPLOADED
from ckanext.hdx_package.helpers.date_helper import DaterangeParser

missing = df.missing
StopOnError = df.StopOnError
Invalid = df.Invalid
get_action = tk.get_action
check_access = tk.check_access

NotAuthorized = tk.NotAuthorized

log = logging.getLogger(__name__)

_DATASET_PREVIEW_FIRST_RESOURCE = 'first_resource'
_DATASET_PREVIEW_RESOURCE_ID = 'resource_id'
_DATASET_PREVIEW_NO_PREVIEW = 'no_preview'
DATASET_PREVIEW_VALUES_LIST = [_DATASET_PREVIEW_FIRST_RESOURCE, _DATASET_PREVIEW_RESOURCE_ID,
                               _DATASET_PREVIEW_NO_PREVIEW]

# Regular expression for validating urls based on
# https://stackoverflow.com/questions/7160737/python-how-to-validate-a-url-in-python-malformed-or-not
# from Django framework

url_regex = re.compile(
    r'^(?:http|ftp)s?://'  # http:// or https://
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
    r'localhost|'  # localhost...
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
    r'(?::\d+)?'  # optional port
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
        err_message = "We couldn't determine your file type. If it is a compressed format (zip, etc), please  \
                      indicate the primary format of the data files inside compressed file."
        errors[key].append(_(err_message))
        raise df.StopOnError()

    return current_format


def to_lower(current_value):
    if current_value:
        return current_value.lower()
    return current_value


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


def hdx_convert_values_to_boolean_for_dataset_preview(key, data, errors, context):
    '''
    convert values to boolean and also sets the dataset_preview to false for the other resources
    '''

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
            data_value_parts = data_value.split('__')  # Example: ['customviz', 0, 'url']
            key_parts = key[-1].split('__')  # Example ['customviz', 'url']
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


def hdx_assume_missing_is_true(value, context):
    if value is missing or value is None:
        return "true"
    return value


def hdx_isodate_to_string_converter(value, context):
    if isinstance(value, datetime.datetime):
        return value.isoformat()
    return None


def reset_on_file_upload(key, data, errors, context):
    resource_name = data.get(key[:-1] + ('name',))
    if resource_name and resource_name == context.get(FILE_WAS_UPLOADED):
        data.pop(key, None)


def hdx_resource_keep_prev_value_unless_sysadmin(key, data, errors, context):
    '''
    By default, this should inject the value from the previous version.
    The exception is if the user is a sysadmin, then the new value is used.
    '''

    if data[key] is missing:
        data.pop(key, None)

    user = context.get('user')
    ignore_auth = context.get('ignore_auth')
    allowed_to_change = ignore_auth or (user and authz.is_sysadmin(user))

    if not allowed_to_change:
        data.pop(key, None)
        resource_id = data.get(key[:-1] + ('id',))
        package_id = data.get(('id',))
        if resource_id:
            specific_key = key[2]
            context_key = 'resource_' + resource_id
            resource_dict = context.get(context_key)
            if not resource_dict:
                resource_dict = __get_previous_resource_dict(context, package_id, resource_id)
                context[context_key] = resource_dict
            if resource_dict:
                old_value = resource_dict.get(specific_key)
                if old_value is not None:
                    data[key] = old_value

    if key not in data:
        raise StopOnError


# def hdx_update_field_if_value_wrapper(context_field, value):
#     def hdx_update_field_if_value(key, data, errors, context):
#         a = 10
#
#     return hdx_update_field_if_value
def hdx_update_microdata(key, data, errors, context):
    if not data.get(key):
        pkg_id = data.get(('id',))
        if pkg_id:
            pkg_dict = __get_previous_package_dict(context, pkg_id)
            if pkg_dict.get(key[0], [])[0].get('in_quarantine', None) and not data.get(key):
                data[key[:2] + ('microdata',)] = False


def hdx_update_in_quarantine_by_microdata(key, data, errors, context):
    if data.get(key):
        pkg_id = data.get(('id',))
        if pkg_id:
            pkg_dict = __get_previous_package_dict(context, pkg_id)
            if len(pkg_dict.get(key[0], [])) > 0:
                if not pkg_dict.get(key[0], [])[0].get('microdata', None) and data.get(key):
                    data[key[:2] + ('in_quarantine',)] = True
            elif data.get(key):
                data[key[:2] + ('in_quarantine',)] = True
        elif data.get(('name',)):
            data[key[:2] + ('in_quarantine',)] = True


def hdx_package_keep_prev_value_unless_field_in_context_wrapper(context_field, resource_level=False):
    def hdx_package_keep_prev_value_unless_field_in_context(key, data, errors, context):
        '''
        By default, this should inject the value from the previous version.
        The exception is if the 'context_field' key is in the context.
        NOTE, we don't check whether user is sysadmin. The api action that set the
        'context_field' should do any checks.
        '''

        if data[key] is missing:
            data.pop(key, None)

        allow_context_field = context.get(context_field)

        if not allow_context_field:
            data.pop(key, None)
            pkg_id = data.get(('id',))

            if resource_level:
                resource_id = data.get(key[:-1] + ('id',))
                if resource_id:
                    resource_dict = __get_previous_resource_dict(context, pkg_id, resource_id) or {}
                    specific_key = key[2]
                    old_value = resource_dict.get(specific_key)
                    if old_value is not None:
                        data[key] = old_value

            # package level
            else:
                if pkg_id:
                    pkg_dict = __get_previous_package_dict(context, pkg_id)
                    old_value = pkg_dict.get(key[0], None)
                    if old_value is not None:
                        data[key] = old_value
        if key not in data:
            raise StopOnError

    return hdx_package_keep_prev_value_unless_field_in_context


def hdx_keep_prev_value_if_empty(key, data, errors, context):
    new_value = data.get(key)
    if new_value is missing or not new_value:
        data.pop(key, None)
        pkg_id = data.get(('id',))
        if pkg_id:
            prev_package_dict = __get_previous_package_dict(context, pkg_id)
            old_value = prev_package_dict.get(key[0], None)
            if old_value:
                data[key] = old_value

    if isinstance(new_value, (str, unicode)) and not new_value.strip():
        data.pop(key, None)

    if key not in data:
        raise StopOnError


def hdx_delete_unless_field_in_context(context_field):
    '''
    :param context_field: the field in the context which tells us if it's ok to allow the value through
    :type context_field: str
    :return:
    :rtype: function
    '''

    def hdx_delete_unless_forced(key, data, errors, context):
        if not context.get(context_field):
            data.pop(key, None)

    return hdx_delete_unless_forced


def hdx_delete_unless_authorized_wrapper(auth_function):
    '''
    :param auth_function: the auth function to run through check_access()
    :type auth_function: str
    :return:
    :rtype: function
    '''

    def hdx_delete_unless_authorized(key, data, errors, context):
        try:
            check_access(auth_function, context, None)
        except NotAuthorized as e:
            data.pop(key, None)

    return hdx_delete_unless_authorized


def hdx_value_in_list_wrapper(allowed_values, allow_missing):
    def hdx_value_in_list(key, data, errors, context):
        value = data[key]
        value_is_missing = not value or value is missing
        if not allow_missing and value_is_missing:
            raise Invalid(_('Value is missing'))
        if not value_is_missing and value not in allowed_values:
            raise Invalid(_('Value not in allowed list'))

    return hdx_value_in_list


def hdx_daterange_possible_infinite_end(key, data, errors, context):
    value = data.get(key)  # type: str
    new_value = DaterangeParser(value).compute_daterange_string(False)
    data[key] = new_value


def hdx_daterange_possible_infinite_end_dataset_date(key, data, errors, context):
    value = data.get(key)  # type: str
    new_value = DaterangeParser(value).compute_daterange_string(False, end_date_ending=True)
    data[key] = new_value


def hdx_convert_old_date_to_daterange(key, data, errors, context):
    value = data[key]
    if value and '[' in value and ']' in value and ' TO ' in value:
        return
    try:
        if value:
            dates_list = value.split('-')
            if dates_list:
                start_date = datetime.datetime.strptime(dates_list[0].strip(), '%m/%d/%Y')
                if len(dates_list) == 2:
                    end_date = datetime.datetime.strptime(dates_list[1].strip(), '%m/%d/%Y')
                else:
                    end_date = start_date
                data[key] = "[{start_date}T00:00:00 TO {end_date}T23:59:59]".format(start_date=start_date.strftime("%Y-%m-%d"),
                                                                                    end_date=end_date.strftime("%Y-%m-%d"))
    except TypeError as e:
        raise df.Invalid(_('Invalid old HDX date format MM/DD/YYYY. Please use [start_datetime TO end_datetime]'))
    except ValueError as e:
        raise df.Invalid(_('Invalid old HDX date format MM/DD/YYYY. Please use [start_datetime TO end_datetime]'))


def hdx_convert_to_json_string(key, data, errors, context):
    value = data[key]
    try:
        data[key] = json.dumps(value)
    except TypeError as e:
        raise df.Invalid(_('Input is not valid'))


def hdx_convert_from_json_string(key, data, errors, context):
    value = data[key]
    try:
        data[key] = json.loads(value)
    except (ValueError, TypeError) as e:
        raise df.Invalid(_('Could not parse JSON'))

# def hdx_autocompute_grouping(key, data, errors, context):
#     current_value = data.get(key)
#     if not current_value or current_value is missing:
#         daterange_value = data.get(key[:-1] + ('daterange_for_data',))
#         if daterange_value and daterange_value is not missing:
#             daterange_parser = DaterangeParser(daterange_value)
#             data[key] = daterange_parser.human_readable()


def __get_previous_resource_dict(context, package_id, resource_id):
    dataset_dict = __get_previous_package_dict(context, package_id)
    return next((r for r in dataset_dict.get('resources', []) if r['id'] == resource_id), None)


def __get_previous_package_dict(context, id):
    context_key = 'hdx_prev_package_dict_' + id
    pkg_dict = context.get(context_key)
    if not pkg_dict:
        pkg_dict = get_action('package_show')(context, {'id': id})
        context[context_key] = pkg_dict

    return pkg_dict or {}


def hdx_resources_not_allowed_if_requested_data(key, data, errors, context):
    if data[key] and ((u'resources', 0, 'url') in data or (u'resources', 0, 'name') in data):
        raise df.Invalid(_('By request - HDX Connect datasets can not store resources'))
