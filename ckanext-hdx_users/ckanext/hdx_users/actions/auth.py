import logging

import ckan.authz as new_authz
import ckan.logic.auth.update as core_auth_update
import ckan.plugins.toolkit as tk

from ckan.types import Context, DataDict, AuthResult
from ckanext.hdx_theme.helpers.auth import _check_hdx_user_permission
from ckanext.hdx_users.helpers.permissions import Permissions
from ckanext.hdx_users.helpers.reset_password import ResetKeyHelper
from ckanext.hdx_users.notifications_subscription_model import get as get_notifications_subscription

log = logging.getLogger(__name__)
_ = tk._

## ORGS
def hdx_send_new_org_request(context, data_dict):
    logged_in = not new_authz.auth_is_anon_user(context)
    if logged_in:
        return {'success': True}
    else:
        return {'success': False, 'msg': _("You must be logged in to send a new organization request.")}


## USERS
def manage_permissions(context, data_dict):
    return {'success': False, 'msg': _('Only sysadmins can view user permission page')}


@tk.auth_allow_anonymous_access
def user_update(context, data_dict):
    if data_dict.get('reset_key'):
        reset_key_helper = ResetKeyHelper(data_dict.get('reset_key'))
        if not reset_key_helper.contains_expiration_time():
            return {'success': False, 'msg': _("Reset key has wrong format")}
        elif reset_key_helper.is_expired():
            return {'success': False, 'msg': _("Reset key no longer valid")}

    return core_auth_update.user_update(context, data_dict)


def notify_users_about_api_token_expiration(context, data_dict):
    return _check_hdx_user_permission(context, Permissions.PERMISSION_MANAGE_BASIC_SCHEDULED_TASKS)

def hdx_send_request_data_auto_approval(context, data_dict):
    return new_authz.is_authorized('package_update', context, {'id': data_dict['package_id']})

def hdx_notifications_subscription_create(context: Context, data_dict: DataDict) -> AuthResult:
    core_data_dict = {
        'id': data_dict['user_id'],
    }
    return core_auth_update.user_update(context, core_data_dict)

def hdx_notifications_subscription_list(context: Context, data_dict: DataDict) -> AuthResult:
    if 'user_id' in data_dict:
        core_data_dict = {
            'id': data_dict['user_id'],
        }
        return core_auth_update.user_update(context, core_data_dict)
    else:
        user_obj = context.get('auth_user_obj') or context.get('user_obj')
        if user_obj and user_obj.is_authenticated:
            return {'success': True}
    return {'success': False}

def hdx_notifications_grouped_subscription_list(context: Context, data_dict: DataDict) -> AuthResult:
    user = context['user']
    if not new_authz.is_sysadmin(user):
        return {'success': False, 'msg': _('Only sysadmins can access this endpoint.')}
    return {'success': True}

def hdx_notifications_subscription_delete(context: Context, data_dict: DataDict) -> AuthResult:
    # user = context['user']
    subscription_obj = get_notifications_subscription(context['session'], data_dict['id'])
    if not subscription_obj:
        return {'success': False, 'msg': _('Subscription obj not found')}

    core_data_dict = {
        'id': subscription_obj.user_id,
    }
    return core_auth_update.user_update(context, core_data_dict)
