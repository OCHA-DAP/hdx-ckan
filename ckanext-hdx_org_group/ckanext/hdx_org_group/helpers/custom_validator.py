'''
Created on May 18, 2020

@author: dan mihaila
'''
import six
import logging

import ckan.authz as authz
import ckan.plugins.toolkit as tk
import ckan.lib.navl.dictization_functions as df
import string
from typing import Any
from urllib.parse import urlparse

from ckan.types import (
    FlattenDataDict, FlattenKey, Context, FlattenErrorDict)

missing = df.missing
StopOnError = df.StopOnError
Invalid = df.Invalid
get_action = tk.get_action
_ = tk._

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


def set_inactive_if_closed_organization(key, data, errors, context):
    value = data.get(key)
    title = data.get(('title',))
    if title:
        if value == 'true' or value == 'True':
            title = title.replace('(closed)', '')
            if not 'inactive' in title:
                if title.endswith(' '):
                    title = title + '(inactive)'
                else:
                    title = title + ' (inactive)'
        else:
            title = title.replace('(closed)', '')
            title = title.replace('(inactive)', '')
            if title.endswith(' '):
                title = title[:-1]
        data[('title',)] = title


def hdx_url_validator(
    key: FlattenKey,
    data: FlattenDataDict,
    errors: FlattenErrorDict,
    context: Context,
) -> Any:
    """Checks that the provided value (if it is present) is a valid URL"""
    url = data.get(key, None)
    if not url:
        return

    try:
        pieces = urlparse(url)
        if pieces.scheme =='http' or pieces.scheme is None:
            errors[key].append(_("Please provide a valid URL that starts with https://"))
            return
        elif all([pieces.scheme, pieces.netloc]) and pieces.scheme in [
            "https",
        ]:
            hostname, port = (
                pieces.netloc.split(":")
                if ":" in pieces.netloc
                else (pieces.netloc, None)
            )
            if set(hostname) <= set(
                string.ascii_letters + string.digits + "-."
            ) and (port is None or port.isdigit()):
                return
    except ValueError:
        # url is invalid
        pass

    errors[key].append(_("Please provide a valid URL"))
