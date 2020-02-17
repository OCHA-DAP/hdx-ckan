import ckan.logic.action.update as _update
import ckan.logic.action.patch as _patch
from ckan.logic import (
    get_action as _get_action,
    check_access as _check_access,
    get_or_bust as _get_or_bust,
)

from ckanext.hdx_package.actions.update import process_skip_validation, process_batch_mode
from ckanext.hdx_package.helpers.constants import BATCH_MODE, BATCH_MODE_KEEP_OLD

def resource_patch(context, data_dict):
    '''
    Cloned from core. It adds a 'no_compute_extra_hdx_show_properties' in contexts to
    make the update faster (less computation in the custom package_show)
    Also used to parse validation parameters (SKIP_VALIDATION) for special cases.

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
    process_batch_mode(context, data_dict)
    process_skip_validation(context, data_dict)

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


def package_patch(context, data_dict):
    '''
    Cloned from core. It's used to parse validation parameters (SKIP_VALIDATION) for special cases

    Patch a dataset (package).

    :param id: the id or name of the dataset
    :type id: string

    The difference between the update and patch methods is that the patch will
    perform an update of the provided parameters, while leaving all other
    parameters unchanged, whereas the update methods deletes all parameters
    not explicitly provided in the data_dict

    You must be authorized to edit the dataset and the groups that it belongs
    to.
    '''
    process_skip_validation(context, data_dict)
    return _patch.package_patch(context, data_dict)


def hdx_mark_broken_link_in_resource(context, data_dict):
    '''
    Does a resource patch to change the 'broken_link' to True. Also sets a field in the context so that the value
    of the 'broken_link' field is kept. Otherwise it would be reset on validation.

    :param id: the id of the resource
    :type id: str
    :return:
    :rtype: dict
    '''

    data_dict['broken_link'] = True
    context['allow_broken_link_field'] = True
    context[BATCH_MODE] = BATCH_MODE_KEEP_OLD
    return _get_action('resource_patch')(context, data_dict)


def hdx_mark_qa_completed(context, data_dict):
    _check_access('hdx_mark_qa_completed', context, data_dict)
    _get_or_bust(data_dict, 'qa_completed')

    context['allow_qa_completed_field'] = True
    context[BATCH_MODE] = BATCH_MODE_KEEP_OLD

    return _get_action('package_patch')(context, data_dict)
