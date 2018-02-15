import ckan.logic.action.update as _update
from ckan.logic import (
    get_action as _get_action,
    check_access as _check_access,
    get_or_bust as _get_or_bust,
)


def resource_patch(context, data_dict):
    '''
    Cloned from core. It adds a 'no_compute_extra_hdx_show_properties' in contexts to
    make the update faster (less computation in the custom package_show)

    Patch a resource

    :param id: the id of the resource
    :type id: string

    The difference between the update and patch methods is that the patch will
    perform an update of the provided parameters, while leaving all other
    parameters unchanged, whereas the update methods deletes all parameters
    not explicitly provided in the data_dict
    '''
    _check_access('resource_patch', context, data_dict)

    context['no_compute_extra_hdx_show_properties'] = True

    show_context = {
        'model': context['model'],
        'session': context['session'],
        'user': context['user'],
        'auth_user_obj': context['auth_user_obj'],
        'no_compute_extra_hdx_show_properties': context.get('no_compute_extra_hdx_show_properties')
    }

    resource_dict = _get_action('resource_show')(
        show_context,
        {'id': _get_or_bust(data_dict, 'id')})

    patched = dict(resource_dict)
    patched.update(data_dict)
    return _update.resource_update(context, patched)
