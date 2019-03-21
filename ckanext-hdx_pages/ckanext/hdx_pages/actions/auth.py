import ckan.logic as logic
import ckanext.hdx_pages.model as pages_model
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
    id = data_dict.get('id')
    if not id or id == '':
        return {'success': False, 'msg': _('Page not found')}

    page = pages_model.Page.get_by_id(id=data_dict.get('id'))
    if page and page.state == 'active':
        return {'success': True}
    else:
        return {'success': False, 'msg': _('Only sysadmins can view non-active custom pages')}
