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
