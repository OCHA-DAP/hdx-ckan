'''
Created on May 18, 2020

@author: dan mihaila
'''
import six
import logging

import ckan.authz as authz
import ckan.plugins.toolkit as tk
import ckan.lib.navl.dictization_functions as df

missing = df.missing
StopOnError = df.StopOnError
Invalid = df.Invalid
get_action = tk.get_action
# check_access = tk.check_access

# NotAuthorized = tk.NotAuthorized

log = logging.getLogger(__name__)


def hdx_org_keep_prev_value_if_empty_unless_sysadmin(key, data, errors, context):
    if data[key] is missing:
        data.pop(key, None)
    user = context.get('user')
    ignore_auth = context.get('ignore_auth')
    allowed_to_change = ignore_auth or (user and authz.is_sysadmin(user))

    if not allowed_to_change:
        data.pop(key, None)
        new_value = data.get(key)
        if new_value is None and isinstance(data.get(('id',)), six.text_type):
            org_id = data.get(('id',))
            if org_id:
                prev_org_dict = get_action('hdx_light_group_show')(context, {'id': org_id})
                old_value = prev_org_dict.get(key[0])
                if old_value:
                    data[key] = old_value
    # if key not in data:
    #     raise StopOnError


def active_if_missing(key, data, errors, context):
    value = data.get(key)
    if value is missing or value is None:
        data[key] = 'active'

