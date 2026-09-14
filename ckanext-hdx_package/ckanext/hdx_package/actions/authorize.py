import logging
import flask
from flask_wtf.csrf import validate_csrf
import ckan.authz as new_authz
import ckan.logic.auth.create as create
import ckan.logic.auth.update as update
import ckan.plugins.toolkit as tk
from ckan.types import Context, DataDict, AuthResult, AuthFunction
from ckanext.hdx_users.helpers.permissions import Permissions

log = logging.getLogger(__name__)
get_action = tk.get_action
auth_allow_anonymous_access = tk.auth_allow_anonymous_access
_ = tk._


def package_create(context, data_dict=None):
    retvalue = True
    if data_dict and 'groups' in data_dict:
        temp_groups = data_dict['groups']
        del data_dict['groups']
        # check original package_create auth
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
        # check original package_create auth
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


# def hdx_create_screenshot_for_cod(context, data_dict=None):
#     '''
#     Only sysadmins are allowed to call this action
#     '''
#     return {'success': False, 'msg': _('Only sysadmins can create a screenshot of a dataset\'s viz')}


@auth_allow_anonymous_access
def hdx_resource_download(context, resource_dict):
    if resource_dict.get('in_quarantine', False):
        return {'success': False, 'msg': _('Only sysadmins can download quarantined resources')}
    return {'success': True}


def hdx_mark_qa_completed(context, data_dict=None):
    username_or_id = context.get('user')
    result = Permissions(username_or_id).has_permission(Permissions.PERMISSION_MANAGE_QA)
    return {'success': result}


def hdx_mark_resource_in_quarantine(context, data_dict=None):
    username_or_id = context.get('user')
    result = Permissions(username_or_id).has_permission(Permissions.PERMISSION_MANAGE_QA)
    return {'success': result}


def hdx_qa_resource_patch(context, data_dict=None):
    '''
    Only sysadmins are allowed to call this action
    '''
    return {'success': False, 'msg': _('Only sysadmins can change the qa script related flags')}


def hdx_fs_check_resource_revise(context, data_dict=None):
    '''
    Only sysadmins are allowed to call this action
    '''
    return {'success': False, 'msg': _('Only sysadmins can change the file structure check info')}

def hdx_qa_hapi_report_view(context, data_dict=None):
    '''
    Only sysadmins are allowed to call this action
    '''
    return {'success': False, 'msg': _('Only sysadmins can change the file structure check info')}

def hdx_cod_update(context, data_dict):
    return _check_hdx_user_permission(context, Permissions.PERMISSION_MANAGE_COD)


# def hdx_dataseries_update(context, data_dict):
#     return _check_hdx_user_permission(context, Permissions.PERMISSION_MANAGE_DATASERIES)


def _check_hdx_user_permission(context, permission):
    username_or_id = context.get('user')
    result = Permissions(username_or_id).has_permission(permission)
    return {'success': result}


def hdx_p_coded_resource_update(context, data_dict):
    username_or_id = context.get('user')
    result = Permissions(username_or_id).has_permission(Permissions.PERMISSION_MANAGE_P_CODES)
    return {'success': result}


def hdx_send_mail_request_tags(context, data_dict):
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


def hdx_mark_resource_in_hapi(context: Context, data_dict: DataDict):
    return _check_hdx_user_permission(context, Permissions.PERMISSION_MANAGE_IN_HAPI_FLAG)


def hdx_request_access(context: Context, data_dict: DataDict):
    """
    Only a logged-in user can request data access.
    """

    user_obj = context.get('auth_user_obj') or context.get('user_obj')
    if user_obj:
        return {'success': True}

    return {'success': False, 'msg': _('Not authorized to perform this request.')}


@tk.chained_auth_function
# @tk.auth_disallow_anonymous_access
def datastore_info(next_auth: AuthFunction, context: Context, data_dict: DataDict) -> AuthResult:
    """
    Override the default authorization for the datastore_info action, so that anonymous users cannot access it
    unless they hold a valid CSRF token (see _datastore_search_for_authenticated_users_or_valid_csrf).
    """
    return _datastore_search_for_authenticated_users_or_valid_csrf(
        'datastore_info', next_auth, context, data_dict)


@tk.chained_auth_function
# @tk.auth_disallow_anonymous_access
def datastore_search(next_auth: AuthFunction, context: Context, data_dict: DataDict) -> AuthResult:
    """
    Override the default authorization for the datastore_search action, so that anonymous users cannot access it
    unless they hold a valid CSRF token (see _datastore_search_for_authenticated_users_or_valid_csrf).
    """
    return _datastore_search_for_authenticated_users_or_valid_csrf(
        'datastore_search', next_auth, context, data_dict)


@tk.chained_auth_function
# @tk.auth_disallow_anonymous_access
def datastore_search_sql(next_auth: AuthFunction, context: Context, data_dict: DataDict) -> AuthResult:
    """
    Override the default authorization for the datastore_search_sql action, so that anonymous users cannot access it.
    """
    return _datastore_search_only_for_authenticated_users(
        'datastore_search_sql', next_auth, context, data_dict)


def _datastore_search_only_for_authenticated_users(
    datastore_action_name: str,
    next_auth: AuthFunction,
    context: Context,
    data_dict: DataDict) -> AuthResult:
    """
    Theoretically, @tk.auth_disallow_anonymous_access should've been enough, but `not context.get('auth_user_obj')` from
    https://github.com/ckan/ckan/blob/095f0779a3f989789c2301e7398bfb27ff0764ed/ckan/authz.py#L232 returns True for
    anonymous users
    """
    if context.get('auth_user_obj').is_authenticated:
        return next_auth(context, data_dict)
    else:
        return {'success': False, 'msg': f'Action {datastore_action_name} requires an authenticated user'}


def _datastore_search_for_authenticated_users_or_valid_csrf(
    datastore_action_name: str,
    next_auth: AuthFunction,
    context: Context,
    data_dict: DataDict) -> AuthResult:
    """
    Same restriction as _datastore_search_only_for_authenticated_users, except an anonymous caller is also
    let through if the request carries a valid CSRF token. This is a deliberate, narrower exception to
    HDX-10974 (used only for datastore_search/datastore_info, not datastore_search_sql) so the resource
    page's Data Dictionary and TDE preview can call these two actions directly from client JS for
    anonymous visitors, who are issued a CSRF token on every page load regardless of login state.
    """
    user_obj = context.get('auth_user_obj') or context.get('user_obj')
    is_authenticated = bool(getattr(user_obj, 'is_authenticated', False))

    if is_authenticated or _request_has_valid_csrf_token():
        return next_auth(context, data_dict)
    else:
        return {'success': False, 'msg': f'Action {datastore_action_name} requires an authenticated user'}


def _request_has_valid_csrf_token() -> bool:
    if not flask.has_request_context():
        return False

    token = flask.request.headers.get('X-CSRFToken') or flask.request.headers.get('X-CSRF-Token')
    if not token:
        return False

    try:
        validate_csrf(token)
    except Exception:
        return False

    return True


def hdx_manage_resource_sdd_report(context: Context, data_dict: DataDict):
    ignore_auth = context.get('ignore_auth', False)
    # we need to allow the `for_update`/`for_edit` context flag so that package_show and resource_show can keep the
    # "sensitive" and "sdd_report" fields when resource data is needed for updates
    for_update_or_edit = context.get('for_update', False) or context.get('for_edit', False)

    username_or_id = context.get('user')
    if not username_or_id:
        return ignore_auth or for_update_or_edit

    has_permission = False
    is_sysadmin = new_authz.is_sysadmin(username_or_id)
    if not is_sysadmin:
        try:
            has_permission = Permissions(username_or_id).has_permission(Permissions.PERMISSION_MANAGE_SDD_REPORT)
        except Exception:
            pass

    return ignore_auth or for_update_or_edit or has_permission or is_sysadmin


def hdx_push_resource_to_datastore(context: Context, data_dict: DataDict) -> AuthResult:
    return {'success': False, 'msg': _('Only sysadmins can directly push resources to datastore')}
