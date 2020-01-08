import logging
import ckan.logic.auth.create as create
import ckan.logic.auth.update as update
from ckan.lib.base import _
import ckan.logic as logic
import ckan.plugins.toolkit as tk


log = logging.getLogger(__name__)
get_action = tk.get_action
auth_allow_anonymous_access = tk.auth_allow_anonymous_access


def package_create(context, data_dict=None):
    retvalue = True
    if data_dict and 'groups' in data_dict:
        temp_groups = data_dict['groups']
        del data_dict['groups']
        #check original package_create auth
        log.debug('Removed groups from data_dict: ' + str(data_dict))
        retvalue = create.package_create(context, data_dict)
        data_dict['groups'] = temp_groups
    else:
        retvalue = create.package_create(context, data_dict)

    return retvalue


def package_update(context, data_dict=None):
    retvalue = True
    if data_dict and 'groups' in data_dict:
        temp_groups = data_dict['groups']
        del data_dict['groups']
        #check original package_create auth
        log.debug('Removed groups from data_dict: ' + str(data_dict))
        retvalue = update.package_update(context, data_dict)
        data_dict['groups'] = temp_groups
    else:
        retvalue = update.package_update(context, data_dict)

    return retvalue


def hdx_resource_id_list(context, data_dict=None):
    '''
    Only sysadmins are allowed to call this action
    '''
    return {'success': False, 'msg': _('Only sysadmins can get the entire list of resource ids')}


def hdx_send_mail_contributor(context, data_dict):
    '''
    Only a logged in user has access.
    '''

    user_obj = context.get('auth_user_obj') or context.get('user_obj')
    if user_obj:
        return {
            'success': True
        }

    return {
        'success': False,
        'msg': _('Not authorized to perform this request')
    }


def hdx_send_mail_members(context, data_dict):
    '''
    Only a logged in user has access and member of dataset's owner_org .
    '''

    user_obj = context.get('auth_user_obj') or context.get('user_obj')
    if user_obj:
        org_members = get_action('hdx_member_list')(context, {'org_id': data_dict.get('org_id')})
        if org_members and org_members.get('is_member'):
            return {
                'success': True
            }

    return {
        'success': False,
        'msg': _('Not authorized to perform this request')
    }


def hdx_create_screenshot_for_cod(context, data_dict=None):
    '''
    Only sysadmins are allowed to call this action
    '''
    return {'success': False, 'msg': _('Only sysadmins can create a screenshot of a dataset\'s viz')}


@auth_allow_anonymous_access
def hdx_resource_download(context, resource_dict):
    if resource_dict.get('in_quarantine', False):
        return {'success': False, 'msg': _('Only sysadmins can download quarantined resources')}
    return {'success': True}
