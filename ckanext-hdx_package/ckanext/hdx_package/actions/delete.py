import ckan.logic
import logging
import ckan.logic.action.delete as core_delete

from ckanext.hdx_package.actions.update import process_batch_mode

_check_access = ckan.logic.check_access
NotFound = ckan.logic.NotFound
_get_or_bust = ckan.logic.get_or_bust
log = logging.getLogger(__name__)


def hdx_dataset_purge(context, data_dict):
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
    model.repo.commit_and_remove()

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

    return result_dict

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

    try:
        if context.get('resource_view').view_type == 'hdx_hxl_preview':
            resource = context.get('resource')
            package_id = resource.package_id
            rebuild(package_id)
    except NotFound:
        log.error("Error: package {} not found.".format(package_id))
    except Exception, e:
        log.error(str(e))