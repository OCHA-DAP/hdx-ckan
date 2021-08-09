import ckan.plugins.toolkit as tk

import ckanext.hdx_dataviz.helpers.helpers as h

h = tk.h

_get_action = tk.get_action


class NotADatavizException(Exception):
    pass


def allowed_to_modify_dataviz(context, package_dict):
    type = None
    is_dataviz_gallery = False
    name = None
    if not package_dict:
        package_obj = context.get('package')
        if package_obj and package_obj.type == 'showcase':
            name = package_obj.name
            type = package_obj.type
            is_dataviz_gallery = package_obj.extras.get('in_dataviz_gallery', False)
    else:
        name = package_dict.get('name')
        type = package_dict.get('type')
        is_dataviz_gallery = package_dict.get('in_dataviz_gallery', False)

    if type == 'showcase' and is_dataviz_gallery:
        allowed = h.has_dataviz_gallery_permission(context.get('user'))
        return allowed

    raise NotADatavizException('Package {} doesn\'t seem to be a dataviz'.format(name))


def _is_editor():
    '''
    Check if the current user is at least editor in some organization
    :return: True if user is at least editor in some org
    :rtype: bool
    '''
    organizations = h.organizations_available('create_dataset')
    if not organizations:
        organizations = h.organizations_available('admin')

    if organizations:
        return True
    return False


# showcase
def showcase_create(context, data_dict):
    return {'success': _is_editor()}


# showcase
def showcase_update(context, data_dict):
    try:
        allowed = allowed_to_modify_dataviz(context, data_dict)
    except NotADatavizException as e:
        allowed = _is_editor()
    return {'success': allowed}


# showcase
def showcase_delete(context, data_dict):
    return showcase_update(context, data_dict)


# showcase
def showcase_package_association_create(context, data_dict):
    return {'success': _is_editor()}


# showcase
def showcase_package_association_delete(context, data_dict):
    return {'success': _is_editor()}


