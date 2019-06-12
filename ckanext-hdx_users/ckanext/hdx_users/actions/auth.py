import ckan.authz as new_authz
from ckan.common import _
from ckanext.hdx_users.helpers.permissions import Permissions


## ORGS
def hdx_send_new_org_request(context, data_dict):
    logged_in = new_authz.auth_is_loggedin_user()
    if logged_in:
        return {'success': True}
    else:
        return {'success': False, 'msg': _("You must be logged in to send a new organization request.")}


def manage_permissions(context, data_dict):
    return {'success': False, 'msg': _('Only sysadmins can view user permission page')}

#
# def hdx_global_settings_show(context, data_dict):
#     '''
#     Only sysadmins and special users are allowed to call this action
#     '''
#     username_or_id = context.get('user')
#     perm_list = [Permissions.PERMISSION_MANAGE_CRISIS,
#                  Permissions.PERMISSION_MANAGE_CAROUSEL,
#                  Permissions.PERMISSION_VIEW_REQUEST_DATA]
#     result = Permissions(username_or_id).has_permissions(perm_list, all=False)
#     return {'success': result}
