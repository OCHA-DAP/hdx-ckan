from ckan.lib.base import _

import logging

log = logging.getLogger(__name__)


def user_extra_create(context, data_dict):
    '''
    A user has access only to his own metainformation (user_extra).
    '''

    user_obj = context.get('auth_user_obj') or context.get('user_obj')
    if user_obj and user_obj.id == data_dict.get('user_id', ''):
        return {
            'success': True
        }

    return {
        'success': False,
        'msg': _('Not authorized to perform this request')
    }


def user_extra_update(context, data_dict):
    '''
    A user has access only to his own metainformation (user_extra).
    '''

    return user_extra_create(context, data_dict)

def user_extra_show(context, data_dict):
    '''
    A user has access only to his own metainformation (user_extra).
    '''

    return user_extra_create(context, data_dict)
