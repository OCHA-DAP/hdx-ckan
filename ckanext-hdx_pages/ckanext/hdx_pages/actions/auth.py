import ckan.logic as logic
import ckan.plugins.toolkit as tk

import ckanext.hdx_pages.model as pages_model
from ckanext.hdx_users.helpers.permissions import Permissions

NotFound = tk.ObjectNotFound
_ = tk._


def page_create(context, data_dict):
    '''
    Only sysadmins are allowed to call this action
    '''
    username_or_id = context.get('user')
    result = Permissions(username_or_id).has_permission(Permissions.PERMISSION_MANAGE_CRISIS)
    return {'success': result}


def admin_page_list(context, data_dict):
    '''
    Only sysadmins are allowed to call this action
    '''
    return page_create(context, data_dict)


def page_update(context, data_dict):
    return page_create(context, data_dict)


def page_delete(context, data_dict):
    return page_create(context, data_dict)


@logic.auth_allow_anonymous_access
def page_show(context, data_dict):
    id = data_dict.get('id')
    if not id or id == '':
        return {'success': False, 'msg': _('Id: missing value')}

    page = pages_model.Page.get_by_id(id=data_dict.get('id'))
    if not page:
        raise NotFound
    if page and page.state == 'active':
        return {'success': True}
    else:
        return {'success': False, 'msg': _('Only sysadmins can view non-active custom pages')}


@logic.auth_allow_anonymous_access
def page_list(context, data_dict):
    return {'success': True}
