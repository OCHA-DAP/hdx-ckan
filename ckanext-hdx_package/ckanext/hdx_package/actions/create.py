'''
Created on Jul 07, 2015

@author: alexandru-m-g
'''

import logging

import ckanext.hdx_package.helpers.analytics as analytics
import ckanext.hdx_package.helpers.geopreview as geopreview
import ckanext.hdx_package.helpers.helpers as helpers
import ckanext.hdx_package.helpers.screenshot as screenshot
from ckanext.hdx_org_group.helpers.org_batch import get_batch_or_generate
from ckanext.hdx_package.actions.update import process_batch_mode, flag_if_file_uploaded
from ckanext.hdx_package.helpers.analytics import is_cod
from ckanext.hdx_package.helpers.constants import BATCH_MODE, BATCH_MODE_DONT_GROUP
from flask import request

import ckan.lib.plugins as lib_plugins
import ckan.logic as logic
import ckan.logic.action.create as core_create
import ckan.plugins as plugins
from ckan.common import _

_get_action = logic.get_action
_check_access = logic.check_access
_get_or_bust = logic.get_or_bust

NotFound = logic.NotFound

log = logging.getLogger(__name__)

@geopreview.geopreview_4_resources
def resource_create(context, data_dict):
    '''
    This runs the 'resource_create' action from core ckan's create.py
    It allows us to do some minor changes and wrap it.
    '''

    process_batch_mode(context, data_dict)
    flag_if_file_uploaded(context, data_dict)

    if data_dict.get('resource_type', '') != 'file.upload':
        #If this isn't an upload, it is a link so make sure we update
        #the url_type otherwise solr will screw everything up
        data_dict['url_type'] = 'api'
    data_dict['size'] = request.content_length
    data_dict['mimetype'] = request.files['upload'].mimetype

    result_dict = core_create.resource_create(context, data_dict)
    return result_dict


@analytics.analytics_wrapper_4_package_create
@geopreview.geopreview_4_packages
def package_create(context, data_dict):
    '''Create a new dataset (package).

    You must be authorized to create new datasets. If you specify any groups
    for the new dataset, you must also be authorized to edit these groups.

    Plugins may change the parameters of this function depending on the value
    of the ``type`` parameter, see the
    :py:class:`~ckan.plugins.interfaces.IDatasetForm` plugin interface.

    :param name: the name of the new dataset, must be between 2 and 100
        characters long and contain only lowercase alphanumeric characters,
        ``-`` and ``_``, e.g. ``'warandpeace'``
    :type name: string
    :param title: the title of the dataset (optional, default: same as
        ``name``)
    :type title: string
    :param private: If ``True`` creates a private dataset
    :type private: bool
    :param author: the name of the dataset's author (optional)
    :type author: string
    :param author_email: the email address of the dataset's author (optional)
    :type author_email: string
    :param maintainer: the name of the dataset's maintainer (optional)
    :type maintainer: string
    :param maintainer_email: the email address of the dataset's maintainer
        (optional)
    :type maintainer_email: string
    :param license_id: the id of the dataset's license, see
        :py:func:`~ckan.logic.action.get.license_list` for available values
        (optional)
    :type license_id: license id string
    :param notes: a description of the dataset (optional)
    :type notes: string
    :param url: a URL for the dataset's source (optional)
    :type url: string
    :param version: (optional)
    :type version: string, no longer than 100 characters
    :param state: the current state of the dataset, e.g. ``'active'`` or
        ``'deleted'``, only active datasets show up in search results and
        other lists of datasets, this parameter will be ignored if you are not
        authorized to change the state of the dataset (optional, default:
        ``'active'``)
    :type state: string
    :param type: the type of the dataset (optional),
        :py:class:`~ckan.plugins.interfaces.IDatasetForm` plugins
        associate themselves with different dataset types and provide custom
        dataset handling behaviour for these types
    :type type: string
    :param resources: the dataset's resources, see
        :py:func:`resource_create` for the format of resource dictionaries
        (optional)
    :type resources: list of resource dictionaries
    :param tags: the dataset's tags, see :py:func:`tag_create` for the format
        of tag dictionaries (optional)
    :type tags: list of tag dictionaries
    :param extras: the dataset's extras (optional), extras are arbitrary
        (key: value) metadata items that can be added to datasets, each extra
        dictionary should have keys ``'key'`` (a string), ``'value'`` (a
        string)
    :type extras: list of dataset extra dictionaries
    :param relationships_as_object: see :py:func:`package_relationship_create`
        for the format of relationship dictionaries (optional)
    :type relationships_as_object: list of relationship dictionaries
    :param relationships_as_subject: see :py:func:`package_relationship_create`
        for the format of relationship dictionaries (optional)
    :type relationships_as_subject: list of relationship dictionaries
    :param groups: the groups to which the dataset belongs (optional), each
        group dictionary should have one or more of the following keys which
        identify an existing group:
        ``'id'`` (the id of the group, string), or ``'name'`` (the name of the
        group, string),  to see which groups exist
        call :py:func:`~ckan.logic.action.get.group_list`
    :type groups: list of dictionaries
    :param owner_org: the id of the dataset's owning organization, see
        :py:func:`~ckan.logic.action.get.organization_list` or
        :py:func:`~ckan.logic.action.get.organization_list_for_user` for
        available values (optional)
    :type owner_org: string

    :returns: the newly created dataset (unless 'return_id_only' is set to True
              in the context, in which case just the dataset id will be returned)
    :rtype: dictionary

    '''

    process_batch_mode(context, data_dict)

    model = context['model']
    user = context['user']

    if 'type' not in data_dict:
        package_plugin = lib_plugins.lookup_package_plugin()
        try:
            # use first type as default if user didn't provide type
            package_type = package_plugin.package_types()[0]
        except (AttributeError, IndexError):
            package_type = 'dataset'
            # in case a 'dataset' plugin was registered w/o fallback
            package_plugin = lib_plugins.lookup_package_plugin(package_type)
        data_dict['type'] = package_type
    else:
        package_plugin = lib_plugins.lookup_package_plugin(data_dict['type'])


    if 'schema' in context:
        schema = context['schema']
    else:
        schema = package_plugin.create_package_schema()

    _check_access('package_create', context, data_dict)

    if 'api_version' not in context:
        # check_data_dict() is deprecated. If the package_plugin has a
        # check_data_dict() we'll call it, if it doesn't have the method we'll
        # do nothing.
        check_data_dict = getattr(package_plugin, 'check_data_dict', None)
        if check_data_dict:
            try:
                check_data_dict(data_dict, schema)
            except TypeError:
                # Old plugins do not support passing the schema so we need
                # to ensure they still work
                package_plugin.check_data_dict(data_dict)

    # Inject a code representing the batch within which this dataset was modified
    if context.get(BATCH_MODE) != BATCH_MODE_DONT_GROUP:
        data_dict['batch'] = get_batch_or_generate(data_dict.get('owner_org'))


    data, errors = lib_plugins.plugin_validate(
        package_plugin, context, data_dict, schema, 'package_create')
    if 'tags' in data:
        data['tags'] = helpers.get_tag_vocabulary(data['tags'])
    if 'groups' in data:
        additions = {'key':'solr_additions','value':helpers.build_additions(data['groups'])}
        if not 'extras' in data:
            data['extras'] = []
        data['extras'].append(additions)

    log.debug('package_create validate_errs=%r user=%s package=%s data=%r',
              errors, context.get('user'),
              data.get('name'), data_dict)

    if errors:
        model.Session.rollback()
        raise logic.ValidationError(errors)

    rev = model.repo.new_revision()
    rev.author = user
    if 'message' in context:
        rev.message = context['message']
    else:
        rev.message = _(u'REST API: Create object %s') % data.get("name")

    if user:
        user_obj = model.User.by_name(user.decode('utf8'))
        if user_obj:
            data['creator_user_id'] = user_obj.id

    # Replace model_save.package_dict_save() call with our wrapped version to be able to save groups
    # pkg = model_save.package_dict_save(data, context)
    from ckanext.hdx_package.actions.update import modified_save
    pkg = modified_save(context, data)

    #pkg = model_save.package_dict_save(data, context)

    # Needed to let extensions know the package and resources ids
    model.Session.flush()
    data['id'] = pkg.id
    if data.get('resources'):
        for index, resource in enumerate(data['resources']):
            resource['id'] = pkg.resources[index].id


    context_org_update = context.copy()
    context_org_update['ignore_auth'] = True
    context_org_update['defer_commit'] = True
    context_org_update['add_revision'] = False
    _get_action('package_owner_org_update')(context_org_update,
                                            {'id': pkg.id,
                                             'organization_id': pkg.owner_org})

    for item in plugins.PluginImplementations(plugins.IPackageController):
        item.create(pkg)

        item.after_create(context, data)

    # Make sure that a user provided schema is not used in create_views
    # and on package_show
    context.pop('schema', None)

    # Create default views for resources if necessary
    if data.get('resources'):
        logic.get_action('package_create_default_resource_views')(
            {'model': context['model'], 'user': context['user'],
             'ignore_auth': True},
            {'package': data})

    if not context.get('defer_commit'):
        model.repo.commit()

    # need to let rest api create
    context["package"] = pkg
    # this is added so that the rest controller can make a new location
    context["id"] = pkg.id
    log.debug('Created object %s' % pkg.name)

    return_id_only = context.get('return_id_only', False)

    output = context['id'] if return_id_only \
        else _get_action('package_show')(context, {'id': context['id']})

    return output


def hdx_create_screenshot_for_cod(context, data_dict):
    _check_access('hdx_create_screenshot_for_cod', context, data_dict)

    id = _get_or_bust(data_dict, 'id')
    dataset_dict = _get_action('package_show')(context, {'id': id})

    if is_cod(dataset_dict) == 'true':
        screenshot.create_screenshot(dataset_dict)


def resource_view_create(context, data_dict):
    ''' Wraps the default resource_view_create ALSO reindexing the package

    :param resource_id: id of the resource
    :type resource_id: string
    :param title: the title of the view
    :type title: string
    :param description: a description of the view (optional)
    :type description: string
    :param view_type: type of view
    :type view_type: string
    :param config: options necessary to recreate a view state (optional)
    :type config: JSON string

    :returns: the newly created resource view
    :rtype: dictionary

    '''

    result = core_create.resource_view_create(context, data_dict)

    reindex_package_on_hdx_hxl_preview_view(data_dict.get('view_type'), context, data_dict)

    return result


def reindex_package_on_hdx_hxl_preview_view(view_type, context, data_dict):

    from ckan.lib.search import rebuild

    if view_type == 'hdx_hxl_preview':
        resource = context.get('resource')

        # resource is in context only when the auth is run. But that doesn't happen for sysadmins
        if resource:
            package_id = resource.package_id
        else:
            resource_id = _get_or_bust(data_dict, 'resource_id')
            model = context['model']
            resource = model.Resource.get(resource_id)
            if resource:
                package_id = resource.package_id
            else:
                package_id = None
        try:
            if package_id:
                rebuild(package_id)
        except NotFound:
            log.error("Error: package {} not found.".format(package_id))
        except Exception, e:
            log.error(str(e))

