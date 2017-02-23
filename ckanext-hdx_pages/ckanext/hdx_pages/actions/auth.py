import ckan.logic as logic
from ckan.lib.base import _


def page_create(context, data_dict):
    '''
    Only sysadmins are allowed to call this action
    '''
    return {'success': False, 'msg': _('Only sysadmins can manage custom pages')}


def page_update(context, data_dict):
    return page_create(context, data_dict)


def page_delete(context, data_dict):
    return page_create(context, data_dict)


@logic.auth_allow_anonymous_access
def page_show(context, data_dict):
    if data_dict.get('state', '') == 'active':
        return {'success': True}
    else:
        return {'success': False, 'msg': _('Only sysadmins can view non-active custom pages')}