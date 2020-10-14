import logging

import ckan.lib.dictization.model_dictize as model_dictize
import ckan.lib.plugins as lib_plugins
import ckan.plugins as plugins
import ckan.plugins.toolkit as tk

from ckanext.hdx_package.actions.get import \
    _additional_hdx_package_show_processing as additional_hdx_package_show_processing

log = logging.getLogger(__name__)
get_action = tk.get_action
_check_access = tk.check_access
NotFound = tk.ObjectNotFound
ValidationError = tk.ValidationError
_get_or_bust = tk.get_or_bust
h = tk.h


def package_list_show_for_reindex(context, dataset_ids):
    '''
    Wraps the default package_show and adds additional information to the resources:
    resource size (for uploaded files) and resource revision timestamp
    '''

    model = context['model']
    context['session'] = model.Session

    dataset_dicts = []
    all_datasets = model.Session.query(model.Package).filter(model.Package.id.in_(dataset_ids)).all()

    for pkg in all_datasets:
        # log.info('Package {}'.format(pkg.id))
        if pkg is None:
            raise NotFound

        context['package'] = pkg
        context['reindexing'] = True

        package_dict = None


        if not package_dict:
            package_dict = model_dictize.package_dictize(pkg, context)
            package_dict_validated = False



        if context.get('for_view'):
            for item in plugins.PluginImplementations(plugins.IPackageController):
                package_dict = item.before_view(package_dict)

        for item in plugins.PluginImplementations(plugins.IPackageController):
            item.read(pkg)

        # for item in plugins.PluginImplementations(plugins.IResourceController):
        #     for resource_dict in package_dict['resources']:
        #         item.before_show(resource_dict)

        if not package_dict_validated:
            package_plugin = lib_plugins.lookup_package_plugin(
                package_dict['type'])
            if 'schema' in context:
                schema = context['schema']
            else:
                schema = package_plugin.show_package_schema()
            if schema and context.get('validate', True):
                package_dict, errors = lib_plugins.plugin_validate(
                    package_plugin, context, package_dict, schema,
                    'package_show')

        for item in plugins.PluginImplementations(plugins.IPackageController):
            item.after_show(context, package_dict)

        additional_hdx_package_show_processing(context, package_dict, just_for_reindexing=True)

        dataset_dicts.append(package_dict)
    return dataset_dicts


def before_indexing_clean_resource_formats(pkg_dict):
    '''
    This is needed when reindexing from CLI: validation is set to false so the package_show()
    (or more precisely ckanext.hdx_package.helpers.reindex_helper.package_list_show_for_reindex())
    doesn't do clean_format()

    :param pkg_dict:
    :type pkg_dict: dict
    '''
    if pkg_dict.get('res_format'):
        new_formats = []
        for format in pkg_dict['res_format']:
            new_format = h.unified_resource_format(format)
            new_formats.append(new_format)
        pkg_dict['res_format'] = new_formats
