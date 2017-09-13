import ckan.logic
import logging
import ckan.logic.action.delete as core_delete
import ckan.plugins.toolkit as toolkit

_check_access = ckan.logic.check_access
NotFound = ckan.logic.NotFound
_get_or_bust = ckan.logic.get_or_bust
log = logging.getLogger(__name__)


def hdx_dataset_purge(context, data_dict):
    # '''
    # Permenantly and completely delete a dataset from HDX
    # '''
    # model = context['model']
    # user = context['user']
    #
    # _check_access('package_delete', context, data_dict)
    #
    # dataset_ref = _get_or_bust(data_dict, 'id')
    # dataset = model.Package.get(unicode(dataset_ref))
    # if dataset is None:
    #     raise NotFound('Dataset "{id}" was not found.'.format(id=dataset_ref))
    #
    # name = dataset.name
    # rev = model.repo.new_revision()
    # try:
    #     dataset.purge()
    #     model.repo.commit_and_remove()
    #     return True
    # except:
    #     return False
    return dataset_purge(context, dict)


def dataset_purge(context, data_dict):
    '''
    This runs the 'dataset_purge' action from core ckan's delete.py
    It allows us to do some minor changes and wrap it.
    '''
    model = context['model']
    id = _get_or_bust(data_dict, 'id')
    pkg = model.Package.get(id)
    is_requested_data_type = _is_requested_data_type(pkg)

    core_delete.dataset_purge(context, data_dict)

    if is_requested_data_type:
        toolkit.get_action("requestdata_request_delete_by_package_id")(context, {'package_id': id})
    log.info('Dataset was purged, id was ' + data_dict.get('id'))


def _is_requested_data_type(entity):
    for extra in entity.extras_list:
        if extra.key == 'is_requestdata_type':
            return 'true' == extra.value
    return False
