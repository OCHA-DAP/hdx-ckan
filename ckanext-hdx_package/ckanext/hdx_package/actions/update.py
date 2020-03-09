'''
Created on Jul 07, 2015

@author: alexandru-m-g
'''

import datetime
import json
import logging

import ckanext.hdx_package.helpers.geopreview as geopreview
import ckanext.hdx_package.helpers.helpers as helpers
from ckanext.hdx_org_group.helpers.org_batch import get_batch_or_generate
from ckanext.hdx_package.helpers.analytics import QACompletedAnalyticsSender
from ckanext.hdx_package.helpers.constants import FILE_WAS_UPLOADED, \
    BATCH_MODE, BATCH_MODE_DONT_GROUP, BATCH_MODE_KEEP_OLD
from ckanext.hdx_package.helpers.file_removal import file_remove
from flask import request

import ckan.lib.dictization.model_save as model_save
import ckan.lib.plugins as lib_plugins
import ckan.lib.munge as munge
import ckan.logic.action.update as core_update
import ckan.plugins as plugins
import ckan.plugins.toolkit as tk
from ckan.common import _

_check_access = tk.check_access
_get_action = tk.get_action

get_or_bust = tk.get_or_bust

NotFound = tk.ObjectNotFound
ValidationError = tk.ValidationError

log = logging.getLogger(__name__)

SKIP_VALIDATION = 'skip_validation'

@geopreview.geopreview_4_resources
def resource_update(context, data_dict):
    '''
    This runs the 'resource_update' action from core ckan's update.py
    It allows us to do some minor changes and wrap it.
    '''

    process_batch_mode(context, data_dict)
    flag_if_file_uploaded(context, data_dict)
    process_skip_validation(context, data_dict)

    # make the update faster (less computation in the custom package_show)
    context['no_compute_extra_hdx_show_properties'] = True

    prev_resource_dict = _fetch_prev_resource_info(context['model'], data_dict)
    prev_resource_is_upload = prev_resource_dict.get('url_type') == 'upload'
    new_file_uploaded = bool(data_dict.get('upload'))

    if data_dict.get('resource_type', '') != 'file.upload':
        #If this isn't an upload, it is a link so make sure we update
        #the url_type otherwise solr will screw everything up
        data_dict['url_type'] = 'api'
    else:
        try:
            if len(request.files) > 0:
                data_dict['size'] = request.content_length
                data_dict['mimetype'] = request.files['upload'].mimetype
        except RuntimeError as re:
            log.debug('This usually happens for tests when there is no HTTP request: ' + unicode(re))

    if data_dict.get('datastore_active', 'false') in ('false', 'False'):
        data_dict['datastore_active'] = False
    else:
        if data_dict.get('datastore_active', 'true') in ('true', 'True'):
            data_dict['datastore_active'] = True
    result_dict = core_update.resource_update(context, data_dict)


    new_resource_is_api = result_dict.get('url_type') == 'api'
    munged_current_res_name = munge.munge_filename(result_dict.get('name'))
    munged_prev_res_name = munge.munge_filename(prev_resource_dict['name'])
    new_file_has_same_name = munged_current_res_name == munged_prev_res_name
    if prev_resource_is_upload and ((new_file_uploaded and not new_file_has_same_name) or new_resource_is_api):
        log.info('Deleting resource {}/{}'.format(prev_resource_dict['id'], prev_resource_dict['name']))
        file_remove(prev_resource_dict['id'], prev_resource_dict['name'], prev_resource_dict['url_type'])
    else:
        log.info('Not deleting resource: prev_resource_is_upload {} / new_file_uploaded {}'
                 '/ new_file_has_same_name {} / new_resource_is_api {}'
                 .format(prev_resource_is_upload, new_file_uploaded, new_file_has_same_name, new_resource_is_api))

    return result_dict


def _fetch_prev_resource_info(model, data_dict):
    prev_resource = model.Resource.get(data_dict.get('id'))
    prev_resource_dict = {
        'id': prev_resource.id,
        'name': prev_resource.name,
        'url_type': prev_resource.url_type
    }
    return prev_resource_dict


@geopreview.geopreview_4_packages
def package_update(context, data_dict):
    '''Update a dataset (package).

    You must be authorized to edit the dataset and the groups that it belongs
    to.

    It is recommended to call
    :py:func:`ckan.logic.action.get.package_show`, make the desired changes to
    the result, and then call ``package_update()`` with it.

    Plugins may change the parameters of this function depending on the value
    of the dataset's ``type`` attribute, see the
    :py:class:`~ckan.plugins.interfaces.IDatasetForm` plugin interface.

    For further parameters see
    :py:func:`~ckan.logic.action.create.package_create`.

    :param id: the name or id of the dataset to update
    :type id: string

    :returns: the updated dataset (if ``'return_package_dict'`` is ``True`` in
              the context, which is the default. Otherwise returns just the
              dataset id)
    :rtype: dictionary

    '''

    process_batch_mode(context, data_dict)
    process_skip_validation(context, data_dict)

    model = context['model']
    user = context['user']
    name_or_id = data_dict.get('id') or data_dict.get('name')
    if name_or_id is None:
        raise ValidationError({'id': _('Missing value')})

    pkg = model.Package.get(name_or_id)
    if pkg is None:
        raise NotFound(_('Package was not found.'))
    context["package"] = pkg
    prev_last_modified = pkg.metadata_modified
    data_dict["id"] = pkg.id
    data_dict['type'] = pkg.type
    if 'groups' in data_dict:
       data_dict['solr_additions'] = helpers.build_additions(data_dict['groups'])

    if 'dataset_confirm_freshness' in data_dict and data_dict['dataset_confirm_freshness'] == 'on':
        data_dict['review_date'] = datetime.datetime.utcnow()

    _check_access('package_update', context, data_dict)

    # get the schema
    package_plugin = lib_plugins.lookup_package_plugin(pkg.type)
    if 'schema' in context:
        schema = context['schema']
    else:
        schema = package_plugin.update_package_schema()

    if 'api_version' not in context:
        # check_data_dict() is deprecated. If the package_plugin has a
        # check_data_dict() we'll call it, if it doesn't have the method we'll
        # do nothing.
        check_data_dict = getattr(package_plugin, 'check_data_dict', None)
        if check_data_dict:
            try:
                package_plugin.check_data_dict(data_dict, schema)
            except TypeError:
                # Old plugins do not support passing the schema so we need
                # to ensure they still work.
                package_plugin.check_data_dict(data_dict)

    # Inject the existing package_creator as it should not be modifiable
    if hasattr(pkg, 'extras'):
        data_dict['package_creator'] = pkg.extras.get('package_creator', data_dict.get('package_creator'))

    # Get previous version of QA COMPLETED
    prev_qa_completed = pkg.extras.get('qa_completed') == 'true'

    # Inject a code representing the batch within which this dataset was modified
    if context.get(BATCH_MODE) == BATCH_MODE_KEEP_OLD:
        try:
            batch_extras = pkg._extras.get('batch')
            if batch_extras and batch_extras.state == 'active':
                data_dict['batch'] = batch_extras.value
        except Exception, e:
            log.info(str(e))
    elif context.get(BATCH_MODE) != BATCH_MODE_DONT_GROUP:
        data_dict['batch'] = get_batch_or_generate(data_dict.get('owner_org'))

    data, errors = lib_plugins.plugin_validate(
        package_plugin, context, data_dict, schema, 'package_update')
    log.debug('package_update validate_errs=%r user=%s package=%s data=%r',
              errors, context.get('user'),
              context.get('package').name if context.get('package') else '',
              data)

    if errors:
        model.Session.rollback()
        raise ValidationError(errors)

    rev = model.repo.new_revision()
    rev.author = user
    if 'message' in context:
        rev.message = context['message']
    else:
        rev.message = _(u'REST API: Update object %s') % data.get("name")

    #avoid revisioning by updating directly
    model.Session.query(model.Package).filter_by(id=pkg.id).update(
        {"metadata_modified": datetime.datetime.utcnow()})
    model.Session.refresh(pkg)

    if 'tags' in data:
        data['tags'] = helpers.get_tag_vocabulary(data['tags'])

    pkg = modified_save(context, data)
    # pkg = model_save.package_dict_save(data, context)

    context_org_update = context.copy()
    context_org_update['ignore_auth'] = True
    context_org_update['defer_commit'] = True
    context_org_update['add_revision'] = False
    _get_action('package_owner_org_update')(context_org_update,
                                            {'id': pkg.id,
                                             'organization_id': pkg.owner_org})

    # Needed to let extensions know the new resources ids
    model.Session.flush()
    if data.get('resources'):
        for index, resource in enumerate(data['resources']):
            resource['id'] = pkg.resources[index].id

    for item in plugins.PluginImplementations(plugins.IPackageController):
        item.edit(pkg)

        item.after_update(context, data)

    if not context.get('defer_commit'):
        model.repo.commit()

    log.debug('Updated object %s' % pkg.name)

    return_id_only = context.get('return_id_only', False)

    # Make sure that a user provided schema is not used on package_show
    context.pop('schema', None)

    # we could update the dataset so we should still be able to read it.
    context['ignore_auth'] = True
    new_data_dict = _get_action('package_show')(context, {'id': data_dict['id']})

    new_qa_completed = new_data_dict.get('qa_completed')
    if new_qa_completed != prev_qa_completed and new_data_dict.get('type') == 'dataset':
        QACompletedAnalyticsSender(new_data_dict, prev_last_modified,
                                   mark_as_set=new_qa_completed).send_to_queue()
        log.debug('new QA COMPLETED value: {}'.format(new_qa_completed))

    return data_dict['id'] if return_id_only else new_data_dict


def package_resource_reorder(context, data_dict):
    '''
    This runs the 'package_resource_reorder' action from core ckan's update.py
    It allows us to do some minor changes and wrap it.
    '''

    process_batch_mode(context, data_dict)

    result_dict = core_update.package_resource_reorder(context, data_dict)

    return result_dict


def process_batch_mode(context, data_dict):
    if BATCH_MODE in data_dict:
        context[BATCH_MODE] = data_dict[BATCH_MODE]
        del data_dict[BATCH_MODE]


def flag_if_file_uploaded(context, data_dict):
    if data_dict.get('upload'):
        context[FILE_WAS_UPLOADED] = data_dict.get('name')


def process_skip_validation(context, data_dict):
    if SKIP_VALIDATION in data_dict:
        context[SKIP_VALIDATION] = data_dict[SKIP_VALIDATION]
        del data_dict[SKIP_VALIDATION]


def modified_save(context, data):
    """
    Wrapper around lib.dictization.model_save.package_dict_save
    """
    groups_key = 'groups'
    if groups_key in data:
        temp_groups = data[groups_key]
        data[groups_key] = None
        pkg = model_save.package_dict_save(data, context)
        data[groups_key] = temp_groups
    else:
        pkg = model_save.package_dict_save(data, context)
    package_membership_list_save(data.get("groups"), pkg, context)
    return pkg


def package_membership_list_save(group_dicts, package, context):
    """
    Overrides lib.dictization.model_save.package_membership_list_save
    """

    allow_partial_update = context.get("allow_partial_update", False)
    if group_dicts is None and allow_partial_update:
        return

    capacity = 'public'
    model = context["model"]
    session = context["session"]
    pending = context.get('pending')
    user = context.get('user')

    members = session.query(model.Member) \
        .filter(model.Member.table_id == package.id) \
        .filter(model.Member.capacity != 'organization')

    group_member = dict((member.group, member)
                        for member in
                        members)
    groups = set()
    for group_dict in group_dicts or []:
        id = group_dict.get("id")
        name = group_dict.get("name")
        capacity = group_dict.get("capacity", "public")
        if capacity == 'organization':
            continue
        if id:
            group = session.query(model.Group).get(id)
        else:
            group = session.query(model.Group).filter_by(name=name).first()
        if group:
            groups.add(group)

    # need to flush so we can get out the package id
    model.Session.flush()

    # Remove any groups we are no longer in
    for group in set(group_member.keys()) - groups:
        member_obj = group_member[group]
        if member_obj and member_obj.state == 'deleted':
            continue

        member_obj.capacity = capacity
        member_obj.state = 'deleted'
        session.add(member_obj)

    # Add any new groups
    for group in groups:
        member_obj = group_member.get(group)
        if member_obj and member_obj.state == 'active':
            continue
        member_obj = group_member.get(group)
        if member_obj:
            member_obj.capacity = capacity
            member_obj.state = 'active'
        else:
            member_obj = model.Member(table_id=package.id,
                                      table_name='package',
                                      group=group,
                                      capacity=capacity,
                                      group_id=group.id,
                                      state='active')
        session.add(member_obj)


def hdx_package_update_metadata(context, data_dict):
    '''
    With the default package_update action from core ckan you need to supply the entire package
    as a parameter, you can't supply just the modified field (or if you do, alot of fields get deleted).
    As specified in the documentation one should first load the package via package_show() and this
    is what this function does.
    '''

    # allowed_fields = ['indicator', 'package_creator', 'methodology',
    #                   'dataset_source', 'dataset_date', 'license_other',
    #                   'license_title', 'caveats', 'name', 'title',
    #                   'last_metadata_update_date', 'dataset_source_code', 'dataset_source',
    #                   'indicator_type', 'indicator_type_code', 'dataset_summary',
    #                   'methodology', 'more_info', 'terms_of_use',
    #                   'validation_notes_and_comments', 'last_data_update_date',
    #                   'groups']

    allowed_fields = ['indicator',
                      'package_creator',
                      'dataset_date',
                      'last_metadata_update_date',
                      'dataset_source_short_name',
                      'source_code',
                      'indicator_type',
                      'indicator_type_code',
                      'more_info',
                      'last_data_update_date',
                      'groups', 'maintainer',
                      'maintainer_email',
                      'data_update_frequency']

    package = _get_action('package_show')(context, data_dict)
    requested_groups = [el.get('id', el.get('name','')) for el in data_dict.get('groups',[])]
    for key, value in data_dict.iteritems():
        if key in allowed_fields:
            package[key] = value
    if not package['notes']:
        package['notes'] = ' '
    package = _get_action('package_update')(context, package)
    db_groups = [el.get('name','') for el in package.get('groups',[]) ]

    if len(requested_groups) != len(db_groups):
        not_saved_groups = set(requested_groups) - set(db_groups)
        log.warn('Indicator: {} - num of groups in request is {} but only {} are in the db. Difference: {}'.
                 format(package.get('name','unknown'),len(requested_groups), len(db_groups), ", ".join(not_saved_groups)))

    return package


def hdx_resource_update_metadata(context, data_dict):
    '''
    With the default resource_update action from core ckan you need to supply the entire resource dict
    as a parameter and you can't supply just a modified field .
    This function first loads the resource via resource_show() and then modifies the respective dict.
    '''

    process_batch_mode(context, data_dict)
    process_skip_validation(context, data_dict)

    # Below params are needed in context so that the URL of the resource is not
    # transformed to a real URL for an uploaded file
    # ( for uploaded files the url field is the filename )
    context['use_cache'] = False
    context['for_edit'] = True

    allowed_fields = ['last_data_update_date', 'shape_info', 'test_field']

    resource_was_modified = False
    resource = _get_action('resource_show')(context, data_dict)

    if data_dict.get('shape_info'):
        data_dict['shape_info'] = geopreview.add_to_shape_info_list(data_dict.get('shape_info'), resource)

    for key, value in data_dict.iteritems():
        if key in allowed_fields:
            resource_was_modified = True
            resource[key] = value

    if resource_was_modified:
        # we don't want the resource update to generate another
        # geopreview transformation
        context['do_geo_preview'] = False
        resource = _get_action('resource_update')(context, resource)

        # if a geopreview was just updated generate a screenshot
        if 'shape_info' in data_dict.keys():
            _get_action('hdx_create_screenshot_for_cod')(context, {'id': resource.get('package_id')})

    return resource


def hdx_resource_delete_metadata(context, data_dict):
    '''
    Removes an entry from the resources extras.
    Nothing happens if the field to be removed doesn't exist in the resource.

    :param id: id of the resource that will be modified
    :type id: str
    :param field_list: list of field names that should be removed
    :type field_list: list
    '''

    # Below params are needed in context so that the URL of the resource is not
    # transformed to a real URL for an uploaded file
    # ( for uploaded files the url field is the filename )
    context['use_cache'] = False
    context['for_edit'] = True

    allowed_fields = ['shape', 'test_field']

    resource_was_modified = False
    field_list = data_dict.get('field_list', [])
    resource = None
    if field_list and len(field_list) > 0:
        resource = _get_action('resource_show')(context, data_dict)
        for field in field_list:
            if field in allowed_fields and field in resource:
                del resource[field]
                resource_was_modified = True

        if resource_was_modified:
            # we don't want the resource update to generate another
            # geopreview transformation
            context['do_geo_preview'] = False
            resource = _get_action('resource_update')(context, resource)

    return resource


def resource_view_update(context, data_dict):
    '''
    Theoretically the core ckan "resource_view_update" should only need the resource_view_id for the update.
    Unfortunately, the auth needs the resource_id as well. So if it's not already there this wrapper
    function injects it.
    '''
    if not data_dict.get('resource_id'):
        model = context['model']
        resource_view = model.ResourceView.get(data_dict.get('id'))
        data_dict['resource_id'] = resource_view.resource_id
    core_update.resource_view_update(context, data_dict)


def package_qa_checklist_update(context, data_dict):
    _check_access('hdx_package_qa_checklist_update', context, data_dict)
    id = get_or_bust(data_dict, 'id')
    del data_dict['id']

    existing_dataset_dict = _get_action('package_show')(context, {'id': id})
    _remove_current_checklist_data(existing_dataset_dict)

    resources_checklist = data_dict.pop('resources', [])
    res_id_to_checklist = {}
    for res_checklist in resources_checklist:
        res_id = get_or_bust(res_checklist, 'id')
        del res_checklist['id']

        # if there's any meaningful data at the resource level (actual checkboxes checked)
        if res_checklist:
            res_id_to_checklist[res_id] = res_checklist

    # if there's any meaningful data (actual checkboxes checked)
    if res_id_to_checklist or data_dict.get('metadata') or data_dict.get('dataProtection') \
        or data_dict.get('checklist_complete'):

        checklist_complete = data_dict.pop('checklist_complete', None)
        if checklist_complete:
            existing_dataset_dict['qa_checklist_completed'] = True
        else:
            existing_dataset_dict['qa_checklist_completed'] = False
            for resource in existing_dataset_dict.get('resources', []):
                checklist = res_id_to_checklist.get(resource['id'])
                if checklist:
                    resource_checklist_string = json.dumps(checklist)
                    resource['qa_checklist'] = resource_checklist_string
                    resource['qa_checklist_num'] = len(checklist)

        data_dict['modified_date'] = datetime.datetime.utcnow().isoformat()

        dataset_checklist_string = json.dumps(data_dict)
        existing_dataset_dict['qa_checklist'] = dataset_checklist_string

    context[BATCH_MODE] = BATCH_MODE_KEEP_OLD
    context['allow_qa_checklist_completed_field'] = True
    context['allow_qa_checklist_field'] = True
    result = _get_action('package_update')(context, existing_dataset_dict)
    return result


def _remove_current_checklist_data(dataset_dict):
    dataset_dict.pop('qa_checklist_completed', None)
    dataset_dict.pop('qa_checklist', None)
    for resource_dict in dataset_dict.get('resources', []):
        resource_dict.pop('qa_checklist', None)
        resource_dict.pop('qa_checklist_num', None)
