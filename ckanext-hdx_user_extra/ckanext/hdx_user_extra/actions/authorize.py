from ckan.lib.base import _

from ckanext.hdx_users.helpers.permissions import USER_EXTRA_FIELD

import logging

log = logging.getLogger(__name__)

SYSADMIN_PROPERTIES = {USER_EXTRA_FIELD}


def user_extra_create(context, data_dict):
    '''
    A user has access only to his own metainformation (user_extra).
    But only sysadmin has access to SYSADMIN_PROPERTIES
    '''
    success = False

    extras_keys = [e['key'] for e in data_dict.get('extras', [])]

    user_obj = context.get('auth_user_obj') or context.get('user_obj')
    if user_obj and user_obj.id == data_dict.get('user_id', '') and SYSADMIN_PROPERTIES.isdisjoint(extras_keys):
        success = True

    if success:
        return {
            'success': True
        }
    else:
        return {
            'success': False,
            'msg': _('Not authorized to perform this request')
        }

def user_extra_update(context, data_dict):

    return user_extra_create(context, data_dict)


def user_extra_show(context, data_dict):

    return user_extra_create(context, data_dict)
