import logging
import ckan.logic.auth.create as _auth_create

import ckan.plugins.toolkit as tk

_ = tk._
log = logging.getLogger(__name__)


def hdx_trigger_screencap(context, data_dict=None):
    '''
    Only sysadmins are allowed to call this action
    '''
    return {'success': False, 'msg': _('Only sysadmins can get the entire list of resource ids')}


def member_delete(context, data_dict):
    '''
    Overriding default member_delete to allow a user to delete himself as a member
    '''
    authenticated_user = context.get('auth_user_obj')

    if data_dict.get('object_type') == 'user':
        user_id_to_be_removed = data_dict.get('object')
        if user_id_to_be_removed == authenticated_user.id or user_id_to_be_removed == authenticated_user.name:
            return {'success': True}

    return _auth_create.member_create(context, data_dict)


def invalidate_data_completeness_for_location(context, data_dict):
    return {'success': False, 'msg': _('Only sysadmins can invalidate data completeness for location')}


## USERS
def hdx_organization_follower_list(context, data_dict):
    return {'success': False, 'msg': _('Only sysadmins can view user permission page')}
