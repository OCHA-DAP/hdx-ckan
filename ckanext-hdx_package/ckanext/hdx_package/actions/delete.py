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

    if pkg and pkg.resources:
        for r in pkg.resources:
            file_remove(r.id, r.url, r.url_type)

    return dataset_purge(context, data_dict)


# needed to overwrite to check access "package_delete"
def dataset_purge(context, data_dict):
    '''
    This runs the 'dataset_purge' action from core ckan's delete.py
    It allows us to do some minor changes and wrap it.
    '''
    model = context['model']
    id = _get_or_bust(data_dict, 'id')
    pkg = model.Package.get(id)
    # is_requested_data_type = _is_requested_data_type(pkg)

    # core_delete.dataset_purge(context, data_dict)

    from sqlalchemy import or_

    context['package'] = pkg
    if pkg is None:
        raise NotFound('Dataset was not found')

    _check_access('package_delete', context, data_dict)

    members = model.Session.query(model.Member) \
        .filter(model.Member.table_id == pkg.id) \
        .filter(model.Member.table_name == 'package')
    if members.count() > 0:
        for m in members.all():
            m.purge()

    for r in model.Session.query(model.PackageRelationship).filter(
        or_(model.PackageRelationship.subject_package_id == pkg.id,
            model.PackageRelationship.object_package_id == pkg.id)).all():
        r.purge()

    pkg = model.Package.get(id)
    # no new_revision() needed since there are no object_revisions created
    # during purge
    pkg.purge()
    try:
        model.repo.commit_and_remove()
    except Exception as ex:
        log.error(ex)

    # if is_requested_data_type:
    #     toolkit.get_action("requestdata_request_delete_by_package_id")(context, {'package_id': id})
    log.info('Dataset was purged, id was ' + data_dict.get('id'))


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
        file_remove(resource.id, resource.url, resource.url_type)
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

    core_delete.resource_view_delete(context, data_dict)

    if resource_view:
        data_dict['resource_id'] = resource_view.resource_id
        reindex_package_on_hdx_hxl_preview_view(resource_view.view_type, context, data_dict)
