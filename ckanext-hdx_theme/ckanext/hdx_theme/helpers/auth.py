import ckan.authz as new_authz
import ckan.logic.auth.create as create

import ckan.plugins.toolkit as tk

from ckan.logic.auth.update import user_generate_apikey
from ckan.logic.auth import get_user_object
from ckanext.hdx_users.helpers.permissions import Permissions

_ = tk._
auth_sysadmins_check = tk.auth_sysadmins_check
NotFound = tk.ObjectNotFound

## ORGS
def _simple_logged_in_auth(fail_message):
    logged_in = new_authz.auth_is_loggedin_user()
    if logged_in:
        return {'success': True}
    else:
        return {'success': False,
                'msg': fail_message}


## ORGS
@auth_sysadmins_check
def group_member_create(context, data_dict):
    try:
        group_dict = tk.get_action('organization_show')(context, {'id': data_dict['id']})
        # if the above call returns we already know it is an organization
        # otherwise a NotFound is raised
        return create.group_member_create(context, data_dict)
    except NotFound:
        # means the specific group is surely not an org or doesn't exist at all
        return {'success': False, 'msg': _('Nobody can add a member to a country in HDX')}


## ORGS
def hdx_basic_user_info(context, data_dict):
    return _simple_logged_in_auth(_("You must be logged in to access basic \
                            organization member info."))


## ORGS
def hdx_send_editor_request_for_org(context, data_dict):
    return _simple_logged_in_auth(_("You must be logged in to send a request \
                            for being an editor."))


# ## ORGS
# def hdx_send_request_membership(context, data_dict):
#     return _simple_logged_in_auth(_("You must be logged in to send a  \
#                             membership request."))


def invalidate_cache_for_groups(context, data_dict):
    return {'success': False, 'msg': _('Only sysadmins can invalidate group cache')}


def invalidate_cache_for_organizations(context, data_dict):
    return {'success': False, 'msg': _('Only sysadmins can invalidate organization cache')}


def invalidate_cached_resource_id_apihighways(context, data_dict):
    return {'success': False, 'msg': _('Only sysadmins can invalidate apihighways cache')}


def invalidate_region(context, data_dict):
    return {'success': False, 'msg': _('Only sysadmins can invalidate region cache')}


def hdx_user_statistics(context, data_dict):
    '''
    Only sysadmins are allowed to call this action
    '''
    return {'success': False, 'msg': _('Only sysadmins can manage custom pages')}


def hdx_push_general_stats(context, data_dict):
    return _check_hdx_user_permission(context, Permissions.PERMISSION_MANAGE_BASIC_SCHEDULED_TASKS)


def hdx_carousel_update(context, data_dict):
    username_or_id = context.get('user')
    result = Permissions(username_or_id).has_permission(Permissions.PERMISSION_MANAGE_CAROUSEL)
    return {'success': result}


def hdx_quick_links_update(context, data_dict):
    username_or_id = context.get('user')
    result = Permissions(username_or_id).has_permission(Permissions.PERMISSION_MANAGE_QUICK_LINKS)
    return {'success': result}


def hdx_request_data_admin_list(context, data_dict):
    username_or_id = context.get('user')
    result = Permissions(username_or_id).has_permission(Permissions.PERMISSION_VIEW_REQUEST_DATA)
    return {'success': result}


@auth_sysadmins_check
def hdx_user_generate_apikey(context, data_dict):
    user_obj = get_user_object(context, data_dict)
    if user_obj.sysadmin:
        return {'success': False, 'msg': _('API keys are disabled for sysadmins')}
    else:
        return user_generate_apikey(context, data_dict)


def _check_hdx_user_permission(context, permission):
    username_or_id = context.get('user')
    result = Permissions(username_or_id).has_permission(permission)
    return {'success': result}
