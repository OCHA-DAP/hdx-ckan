import ckan.logic.action.update as _update

import ckan.plugins.toolkit as tk

import ckanext.hdx_package.helpers.resource_triggers.fs_check as fs_check
from ckan.types import Context, DataDict
from ckanext.hdx_package.actions.update import process_skip_validation, process_batch_mode, package_update, \
    SKIP_VALIDATION
from ckanext.hdx_package.helpers.analytics import QAQuarantineAnalyticsSender
from ckanext.hdx_package.helpers.constants import BATCH_MODE, BATCH_MODE_KEEP_OLD, NO_DATA
from ckanext.hdx_package.helpers.s3_version_tagger import tag_s3_version_by_resource_id
from ckanext.hdx_package.helpers.resource_triggers.geopreview import delete_geopreview_layer

NotFound = tk.ObjectNotFound
ValidationError = tk.ValidationError

_check_access = tk.check_access
_get_action = tk.get_action
_get_or_bust = tk.get_or_bust


# @fs_check.fs_check_4_resources
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
    Does a resource patch to change the 'broken_link' to True or False. Also sets a field in the context so that the value
    of the 'broken_link' field is kept. Otherwise it would be reset on validation.

    :param id: the id of the resource
    :type id: str
    :return:
    :rtype: dict
    '''

    resource_id = data_dict.get('id')
    broken_link = data_dict.get('broken_link', True)
    if resource_id:
        resource_dict = _get_action('resource_show')(context, {'id': resource_id})
        package_id = resource_dict.get('package_id')
        if not package_id:
            raise NotFound("dataset was not found")
        data_revise_dict = {
            "match": {"id": package_id},
            'update__resources__' + resource_id: {'broken_link': broken_link}
        }
        # data_dict['broken_link'] = True
        context['allow_broken_link_field'] = True
        context[BATCH_MODE] = BATCH_MODE_KEEP_OLD
        # return _get_action('resource_patch')(context, data_dict)
        return _get_action('package_revise')(context, data_revise_dict)
    else:
        raise NotFound("resource id was not provided")


def hdx_mark_qa_completed(context, data_dict):
    '''
    This action uses PERMISSIONS! Please be careful if changing the scope of its changes !
    '''
    _check_access('hdx_mark_qa_completed', context, data_dict)
    _get_or_bust(data_dict, 'qa_completed')

    context['ignore_auth'] = True
    context['allow_qa_completed_field'] = True
    context[BATCH_MODE] = BATCH_MODE_KEEP_OLD

    if 'id' in data_dict and 'qa_completed' in data_dict:
        data_revise_dict = {
            "match": {"id": data_dict.get('id')},
            "update": {'qa_completed': data_dict.get('qa_completed')}
        }
    else:
        raise NotFound("package id or key were not provided")
    return _get_action('package_revise')(context, data_revise_dict)

    # return _get_action('package_patch')(context, data_dict)


def hdx_mark_resource_in_quarantine(context, data_dict):
    '''
    This action uses PERMISSIONS! Please be careful if changing the scope of its changes !
    '''
    _check_access('hdx_mark_resource_in_quarantine', context, data_dict)
    new_data_dict = {
        'id': _get_or_bust(data_dict, 'id'),
        'in_quarantine': _get_or_bust(data_dict, 'in_quarantine')

    }
    context['ignore_auth'] = True
    result = _get_action('hdx_qa_resource_patch')(context, new_data_dict)
    return result


def hdx_qa_resource_patch(context, data_dict):
    _check_access('hdx_qa_resource_patch', context, data_dict)

    context['allow_resource_qa_script_field'] = True
    context[BATCH_MODE] = BATCH_MODE_KEEP_OLD

    resource_dict = _get_action('resource_show')(context, {'id': data_dict.get('id')})
    dataset_dict = _get_action('package_show')(context, {'id': resource_dict['package_id']})

    pkg_id = resource_dict.get('package_id')
    data_revise_dict = {'match': {'id': pkg_id}}

    _do_quarantine_related_processing_if_needed(context, data_dict, data_revise_dict, dataset_dict, resource_dict)

    update_resource_dict = {key: value for key, value in data_dict.items() if key != 'id'}
    if update_resource_dict:
        data_revise_dict['update__resources__' + resource_dict.get('id')] = update_resource_dict

    if len(data_revise_dict.keys()) <= 1:
        raise NotFound("resource id, key or value were not provided")
    revise_response = _get_action('package_revise')(context, data_revise_dict)
    package = revise_response.get('package', {})
    resource_dict = next((res for res in package.get('resources', []) if res.get('id') == resource_dict['id']), None)
    return resource_dict


def _do_quarantine_related_processing_if_needed(context, data_dict, data_revise_dict, dataset_dict, resource_dict):
    new_quarantine_value = data_dict.get('in_quarantine')
    if new_quarantine_value is not None:
        # if new quarantine value is either true or false send analytics if value changed
        analytics_sender = QAQuarantineAnalyticsSender(dataset_dict,
                                                       resource_dict.get('id'), new_quarantine_value == 'true')
        if analytics_sender.should_send_analytics_event():
            analytics_sender.send_to_queue()

        # if new quarantine value is either true or false tag it in S3 as sensitive and with dataset name
        if resource_dict.get('url_type', None) == 'upload':
            tag_s3_version_by_resource_id(
                {
                    'model': context['model'],
                    'user': context['user'],
                    'auth_user_obj': context['auth_user_obj'],
                },
                data_dict['id'],
                data_dict['in_quarantine'] == 'true',
                resource_dict.get('url'),
                dataset_dict.get('name')
            )
    _remove_geopreview_data(new_quarantine_value, data_revise_dict, resource_dict)

def _remove_geopreview_data(new_quarantine_value, data_revise_dict, resource_dict):
    if new_quarantine_value == 'true' and resource_dict.get('shape_info'):
        resource_id = resource_dict['id']
        data_revise_dict['filter'] = [
            "-resources__" + resource_id + "__shape_info"
        ]
        delete_geopreview_layer(resource_id)


def hdx_fs_check_resource_revise(context, data_dict):
    _check_access('hdx_fs_check_resource_revise', context, data_dict)

    context['allow_fs_check_field'] = True
    context['fs_check_is_upload_xls'] = False
    context[BATCH_MODE] = BATCH_MODE_KEEP_OLD
    pkg_id = data_dict.get('package_id')
    res_id = data_dict.get('id')
    key = data_dict.get('key')
    value = data_dict.get('value')

    data_revise_dict = {
        "match": {"id": pkg_id},
        'update__resources__' + res_id[:5]: {key: value}
    }
    return _get_action('package_revise')(context, data_revise_dict)


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


@tk.side_effect_free
def hdx_fs_check_resource_reset(context, data_dict):
    _check_access('hdx_fs_check_resource_revise', context, data_dict)

    context['allow_fs_check_field'] = True
    pkg_id = data_dict.get('package_id')
    res_id = data_dict.get('id')
    key = data_dict.get('key', 'fs_check_info')

    data_revise_dict = {
        "match": {"id": pkg_id},
        'update__resources__' + res_id[:5]: {key: ''}
    }
    return _get_action('package_revise')(context, data_revise_dict)


@tk.side_effect_free
def hdx_fs_check_package_reset(context, data_dict):
    _check_access('hdx_fs_check_resource_revise', context, data_dict)
    pkg_id = data_dict.get('package_id')
    pkg_dict = _get_action('package_show')(context, {'id': pkg_id})
    if pkg_dict.get('resources'):
        key = data_dict.get('key', 'fs_check_info')

        context['allow_fs_check_field'] = True
        data_revise_dict = {"match": {"id": pkg_id}}
        for res in pkg_dict.get('resources'):
            data_revise_dict['update__resources__' + res.get('id')[:5]] = {key: ''}
        return _get_action('package_revise')(context, data_revise_dict)

    raise NotFound("package doesn't contain resources or not found")


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
    context[SKIP_VALIDATION] = True

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


def hdx_p_coded_resource_update(context, data_dict):
    _check_access('hdx_p_coded_resource_update', context, data_dict)
    resource_id = _get_or_bust(data_dict, 'id')
    p_coded = data_dict['p_coded']
    show_context = {
        'model': context['model'],
        'session': context['session'],
        'user': context['user'],
        'no_compute_extra_hdx_show_properties': context.get('no_compute_extra_hdx_show_properties')
    }
    resource_dict = _get_action('resource_show')(show_context, {'id': resource_id})
    data_revise_dict = {
        'match': {
            'id': resource_dict['package_id']
        },
        'update__resources__' + resource_id: {
            'p_coded': p_coded
        }
    }
    context['ignore_auth'] = True
    context[SKIP_VALIDATION] = True
    result = _get_action('package_revise')(context, data_revise_dict)
    return next((r for r in result['package']['resources'] if r['id'] == resource_id), None)


def hdx_mark_resource_in_hapi(context: Context, data_dict: DataDict):
    """
    This action uses PERMISSIONS! Please be careful if changing the scope of its changes!
    """
    _check_access('hdx_mark_resource_in_hapi', context, data_dict)

    if 'id' in data_dict and 'in_hapi' in data_dict:
        new_data_dict = {
            'id': _get_or_bust(data_dict, 'id'),
            'in_hapi': _get_or_bust(data_dict, 'in_hapi')
        }
    else:
        raise NotFound('Resource ID or key were not provided.')

    context['ignore_auth'] = True
    context['allow_resource_in_hapi_field'] = True

    return _get_action('resource_patch')(context, new_data_dict)
