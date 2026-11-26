import logging

import ckan.logic as logic
import ckan.logic.action.delete as core_delete
import ckanext.hdx_package.helpers.resource_triggers.common
from ckanext.hdx_package.actions.update import process_batch_mode
from ckanext.hdx_package.actions.create import reindex_package_on_hdx_hxl_preview_view
from ckanext.hdx_package.helpers.file_removal import file_remove

from ckanext.hdx_package.helpers.resource_triggers import VERSION_CHANGE_ACTIONS

_check_access = logic.check_access
NotFound = logic.NotFound
_get_or_bust = logic.get_or_bust
log = logging.getLogger(__name__)
_get_action = logic.get_action


@ckanext.hdx_package.helpers.resource_triggers.common.trigger_4_dataset_delete(VERSION_CHANGE_ACTIONS)
def hdx_dataset_purge(context, data_dict):
    _check_access('package_delete', context, data_dict)

    model = context['model']
    id = _get_or_bust(data_dict, 'id')
    pkg = model.Package.get(id)

    _get_action('package_delete')(context, {'id': id})

    # Files and datastore tables can't be restored, so remove them only after the purge is committed
    resources = [(r.id, r.url, r.url_type) for r in pkg.resources] if pkg else []

    # package_delete was checked above, the same check as HDX's dataset_purge auth function
    core_delete.dataset_purge(dict(context, ignore_auth=True), data_dict)
    log.info('Dataset was purged, id was ' + id)

    for resource_id, resource_url, resource_url_type in resources:
        file_remove(resource_id, resource_url, resource_url_type)
        try:
            # The resource is purged, so datastore_delete's resource_update auth check can't find it
            _get_action('datastore_delete')(
                {'model': model, 'session': model.Session, 'user': context.get('user'), 'ignore_auth': True},
                {'resource_id': resource_id, 'force': True})
        except NotFound:
            log.info('Resource {} not found in datastore while datastore_delete.'.format(resource_id))


def resource_delete(context, data_dict):
    '''
    This runs the 'resource_delete' action from core ckan's delete.py
    It allows us to do some minor changes and wrap it.
    '''
    process_batch_mode(context, data_dict)
    id = _get_or_bust(data_dict, 'id')

    context['do_geo_preview'] = False
    context['defer_commit'] = True
    # result_dict = core_delete.resource_delete(context, data_dict)
    model = context['model']
    try:
        resource = model.Resource.get(id)
        filter_key = "-resources__" + id
        data_revise_dict = {
            "match": {"id": resource.package_id},
            "filter": [filter_key]
        }
        _get_action('package_revise')(context, data_revise_dict)
        # _resource_purge(context, data_dict)
        # file_remove(resource.id, resource.url, resource.url_type)
        # _datastore_delete(context, resource.id, resource.datastore_active)
        model.repo.commit()
    except Exception as ex:
        log.error('Exception while trying to delete resource:' + str(ex))
        model.Session.rollback()

def _is_requested_data_type(entity):
    for extra in entity.extras_list:
        if extra.key == 'is_requestdata_type':
            return 'true' == extra.value
    return False


def resource_view_delete(context, data_dict):
    ''' Wraps the default resource_view_delete ALSO reindexing the package

    :param id: the id of the resource_view
    :type id: string

    '''
    model = context['model']
    resource_view_id = _get_or_bust(data_dict, 'id')
    resource_view = model.ResourceView.get(resource_view_id)

    result = core_delete.resource_view_delete(context, data_dict)

    if resource_view:
        data_dict['resource_id'] = resource_view.resource_id
        reindex_package_on_hdx_hxl_preview_view(resource_view.view_type, context, data_dict)

    return result
