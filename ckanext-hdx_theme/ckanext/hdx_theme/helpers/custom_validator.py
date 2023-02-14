import re

import ckan.authz as authz
import ckan.lib.navl.dictization_functions as df
import ckan.plugins.toolkit as tk

_ = tk._
Invalid = tk.Invalid
StopOnError = tk.StopOnError
_missing = tk.missing


def general_value_in_list(value_list, allow_not_selected, not_selected_value='-1'):

    def verify_value_in_list(key, data, errors, context):

        value = data.get(key)
        if allow_not_selected and value == not_selected_value:
            del data[key]
            # Don't go further in the validation chain. Ex: convert to extras doesn't need to be called
            raise df.StopOnError
        if not value or value not in value_list:
            raise df.Invalid(_('needs to be a value from the list'))

    return verify_value_in_list


# used for api token validations
def doesnt_exceed_max_validity_period(key, data, errors, context):
    expires_in = data.get(key, 0)
    unit = data.get(('unit',), 0)
    user = data.get(('user',))
    max_days = 180 if authz.is_sysadmin(user) else 365
    try:
        unit = int(unit) # make sure the unit is an integer
    except ValueError as ve:
        raise df.Invalid(_('Unit needs to be an integer value'))
    seconds = expires_in * unit
    max_seconds = max_days * 24 * 60 * 60
    if seconds > max_seconds:
        raise df.Invalid(_('Token needs to expire in maximum {} days'.format(max_days)))


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


def hdx_is_url(key, data, errors, context):
    value = data.get(key)
    match_result = re.match(url_regex, value)
    if match_result is None:
        errors[key].append(_('Value is not a URL'))
        raise StopOnError


def hdx_check_string_length_wrapper(limit=12):
    def check_string_length(value, context):
        if len(value) > limit:
            raise Invalid(_('The text shouldn\'t be longer than {} chars').format(limit))
        return value

    return check_string_length


def hdx_clean_field_based_on_other_field_wrapper(other_field_name):
    def _clean_field(key, data, errors, context):
        url_value = data.get((other_field_name,))
        if url_value is _missing or not url_value:
            data[key] = ''
    return _clean_field
