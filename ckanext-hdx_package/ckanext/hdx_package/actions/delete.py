import os
import logging

import ckan.logic as logic
import ckan.logic.action.delete as core_delete
from ckan.lib import uploader

from ckanext.s3filestore.uploader import S3ResourceUploader

from ckanext.hdx_theme.helpers.config import is_s3filestore_enabled
from ckanext.hdx_package.actions.update import process_batch_mode
from ckanext.hdx_package.actions.create import reindex_package_on_hdx_hxl_preview_view


_check_access = logic.check_access
NotFound = logic.NotFound
_get_or_bust = logic.get_or_bust
log = logging.getLogger(__name__)
_get_action = logic.get_action


def file_remove(resource):

    def file_remove_local(resource):
        id = resource.id
        storage_path = uploader.get_storage_path()
        directory = os.path.join(storage_path, 'resources', id[0:3], id[3:6])
        filepath = os.path.join(directory, id[6:])

        # remove file and its directory tree
        try:
            # remove file
            os.remove(filepath)
            # remove empty parent directories
            os.removedirs(directory)
            log.info(u'File %s is deleted.' % filepath)
        except OSError, e:
            log.debug(u'Error: %s - %s.' % (e.filename, e.strerror))

        pass

    def file_remove_s3(resource):
        try:
            if resource.url_type == 'upload':
                uploader = S3ResourceUploader({})
                filepath = uploader.get_path(resource.id, resource.name)
                uploader.clear_key(filepath)
        except Exception, e:
            msg = 'Couldn\'t delete file from S3'
            log.warning(msg + str(e))

    if is_s3filestore_enabled():
        file_remove_s3(resource)
    else:
        file_remove_local(resource)


def hdx_dataset_purge(context, data_dict):
    _check_access('package_delete', context, data_dict)

    model = context['model']
    id = _get_or_bust(data_dict, 'id')
    pkg = model.Package.get(id)

    _get_action('package_delete')(context, {'id': id})

    if pkg and pkg.resources:
        for r in pkg.resources:
            file_remove(r)

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
    except Exception, ex:
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

    result_dict = core_delete.resource_delete(context, data_dict)

    _resource_purge(context, data_dict)
    return result_dict

def _resource_purge(context, data_dict):
    model = context['model']
    resource = model.Resource.get(data_dict.get('id'))
    file_remove(resource)


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
    from ckan.lib.search import rebuild

    core_delete.resource_view_delete(context, data_dict)

    resource_view = context.get('resource_view')
    if resource_view:
        reindex_package_on_hdx_hxl_preview_view(resource_view.view_type, context, data_dict)

