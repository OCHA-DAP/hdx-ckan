import ckan.logic.action.update as _update

import ckan.plugins.toolkit as tk

from ckanext.hdx_package.actions.update import process_skip_validation, process_batch_mode, package_update
from ckanext.hdx_package.helpers.constants import BATCH_MODE, BATCH_MODE_KEEP_OLD, NO_DATA
from ckanext.hdx_package.helpers.s3_version_tagger import tag_s3_version_by_resource_id

NotFound = tk.ObjectNotFound
ValidationError = tk.ValidationError

_check_access = tk.check_access
_get_action = tk.get_action
_get_or_bust = tk.get_or_bust


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
    Also, changed so that it now calls "our" package_update instead of the core package_update.

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

    # Original package patch from CKAN
    _check_access('package_patch', context, data_dict)

    show_context = {
        'model': context['model'],
        'session': context['session'],
        'user': context['user'],
        'auth_user_obj': context['auth_user_obj'],
    }

    package_dict = _get_action('package_show')(
        show_context,
        {'id': _get_or_bust(data_dict, 'id')})

    patched = dict(package_dict)
    patched.update(data_dict)
    patched['id'] = package_dict['id']

    # slightly modified to call "our" package_update
    return package_update(context, patched)
    # END - Original package patch from CKAN


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


def hdx_qa_resource_patch(context, data_dict):
    _check_access('hdx_qa_resource_patch', context, data_dict)

    context['allow_resource_qa_script_field'] = True
    context[BATCH_MODE] = BATCH_MODE_KEEP_OLD

    if data_dict.get('in_quarantine') is not None:
        tag_s3_version_by_resource_id(
            {
                'model': context['model'],
                'user': context['user'],
                'auth_user_obj': context['auth_user_obj'],
            },
            data_dict['id'],
            data_dict['in_quarantine'] == 'true'
        )

    return _get_action('resource_patch')(context, data_dict)


def hdx_qa_package_revise_resource(context, data_dict):
    _check_access('hdx_qa_resource_patch', context, data_dict)

    pkg_id = data_dict.get('id') or data_dict.get('package_id')
    key = data_dict.get('key')
    value = data_dict.get('value')
    if pkg_id is None or key is None or value is None:
        raise NotFound("package id, key or value were not provided")
    pkg_dict = _get_action('package_show')(context, {'id': pkg_id})

    context['allow_resource_qa_script_field'] = True
    context[BATCH_MODE] = BATCH_MODE_KEEP_OLD

    data_revise_dict = {
        "match": {"id": pkg_id}
    }
    # if 'resources' in pkg_dict and len(pkg_dict.get('resources'))>0:
    for res in pkg_dict.get('resources'):
        data_revise_dict['update__resources__' + str(res.get('position'))] = {key: value}

    return _get_action('package_revise')(context, data_revise_dict)


def hdx_dataseries_link(context, data_dict):
    _check_access('hdx_dataseries_update', context, data_dict)
    name_or_id = _get_or_bust(data_dict, 'id')
    dataseries_name = _get_or_bust(data_dict, 'dataseries_name')
    return _manage_dataseries_link(context, name_or_id, dataseries_name)


def hdx_dataseries_unlink(context, data_dict):
    _check_access('hdx_dataseries_update', context, data_dict)
    name_or_id = _get_or_bust(data_dict, 'id')
    return _manage_dataseries_link(context, name_or_id, dataseries_name=None)


def _manage_dataseries_link(context, dataset_name_or_id, dataseries_name=None):
    context['ignore_auth'] = True

    model = context['model']
    pkg = model.Package.get(dataset_name_or_id)

    if not pkg:
        raise NotFound('Dataset {} was not found'.format(dataset_name_or_id))

    data_revise_dict = {
        'match': {
            'id': pkg.id
        },
        'update': {
            'dataseries_name': dataseries_name if dataseries_name else NO_DATA
        }
    }
    result = _get_action('package_revise')(context, data_revise_dict)
    return result['package']
