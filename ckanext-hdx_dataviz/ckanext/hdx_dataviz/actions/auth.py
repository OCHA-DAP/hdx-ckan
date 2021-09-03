import ckan.plugins.toolkit as tk

import ckanext.hdx_dataviz.helpers.helpers as h

_get_action = tk.get_action
_get_or_bust = tk.get_or_bust
NotFound = tk.ObjectNotFound


class NotADatavizException(Exception):
    pass


def allowed_to_modify_dataviz(context, package_dict):
    type = None
    is_dataviz_gallery = False
    name = None
    package_obj = context.get('package')

    # if the dataviz is in the context
    if package_obj:
        if package_obj.type == 'showcase':
            name = package_obj.name
            type = package_obj.type
            is_dataviz_gallery = package_obj.extras.get('in_dataviz_gallery', False)
    # if we have it is a full package_dict and not just the id
    elif package_dict.get('type'):
        name = package_dict.get('name')
        type = package_dict.get('type')
        is_dataviz_gallery = package_dict.get('in_dataviz_gallery', False)
    # if we have at least the id
    else:
        package_id = _get_or_bust(package_dict, 'id')
        model = context.get('model')
        package_obj = model.Package.get(package_id)
        if not package_obj:
            raise NotFound('No showcase could be found with id {}'.format(package_id))
        name = package_obj.name
        type = package_obj.type
        is_dataviz_gallery = package_obj.extras.get('in_dataviz_gallery', False)

    if type == 'showcase' and is_dataviz_gallery:
        allowed = h.has_dataviz_gallery_permission(context.get('user'))
        return allowed

    raise NotADatavizException('Package {} doesn\'t seem to be a dataviz'.format(name))


def _is_editor(context):
    '''
    Check if the current user is at least editor in some organization
    :return: True if user is at least editor in some org
    :rtype: bool
    '''
    def __organizations_available(permission):
        return _get_action('organization_list_for_user')({'user': context.get('user')}, {'permission': permission})

    organizations = __organizations_available('create_dataset')
    if not organizations:
        organizations = __organizations_available('admin')

    if organizations:
        return True
    return False


# showcase
def showcase_create(context, data_dict):
    return {'success': _is_editor(context)}


# showcase
def showcase_update(context, data_dict):
    try:
        allowed = allowed_to_modify_dataviz(context, data_dict)
    except NotADatavizException as e:
        allowed = _is_editor(context)
    return {'success': allowed}


# showcase
def showcase_delete(context, data_dict):
    return showcase_update(context, data_dict)


# showcase
def showcase_package_association_create(context, data_dict):
    return {'success': _is_editor(context)}


# showcase
def showcase_package_association_delete(context, data_dict):
    return {'success': _is_editor(context)}
