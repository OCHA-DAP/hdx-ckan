import logging
import socket
import json

import ckan
import ckan.logic as logic
import ckan.lib.dictization.model_dictize as model_dictize
import ckan.plugins as plugins
import ckan.lib.search as search
import ckan.lib.plugins as lib_plugins
import ckanext.hdx_theme.util.jql as jql

from paste.deploy.converters import asbool

from ckanext.hdx_package.actions.get import _should_manually_load_property_value, _get_resource_hdx_relative_url, \
    _get_resource_revison_timestamp, _get_resource_filesize, GEODATA_FORMATS
from ckanext.hdx_search.actions.actions import hdx_get_package_showcase_id_list

log = logging.getLogger(__name__)
get_action = logic.get_action
_check_access = logic.check_access
NotFound = logic.NotFound
ValidationError = logic.ValidationError
_get_or_bust = logic.get_or_bust


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






        # added because showcase schema validation is generating "ckan.lib.navl.dictization_functions.Missing"
        if 'tracking_summary' in package_dict and not package_dict.get('tracking_summary'):
            del package_dict['tracking_summary']

        if package_dict.get('type') == 'dataset': # this shouldn't be executed from showcases
            for resource_dict in package_dict.get('resources', []):
                if _should_manually_load_property_value(context, resource_dict, 'size'):
                    resource_dict['size'] = _get_resource_filesize(resource_dict)

                if _should_manually_load_property_value(context, resource_dict, 'revision_last_updated'):
                    resource_dict['revision_last_updated'] = _get_resource_revison_timestamp(resource_dict)

                if _should_manually_load_property_value(context, resource_dict, 'hdx_rel_url'):
                    resource_dict['hdx_rel_url'] = _get_resource_hdx_relative_url(resource_dict)

            # downloads_list = (res['tracking_summary']['total'] for res in package_dict.get('resources', []) if
            #                   res.get('tracking_summary', {}).get('total'))
            # package_dict['total_res_downloads'] = sum(downloads_list)

            if _should_manually_load_property_value(context, package_dict, 'total_res_downloads'):
                total_res_downloads = jql.downloads_per_dataset_all_cached().get(package_dict['id'], 0)
                log.debug('Dataset {} has {} downloads'.format(package_dict['id'], total_res_downloads))
                package_dict['total_res_downloads'] = total_res_downloads

            if _should_manually_load_property_value(context, package_dict, 'pageviews_last_14_days'):
                pageviews_last_14_days = jql.pageviews_per_dataset_last_14_days_cached().get(package_dict['id'], 0)
                log.debug('Dataset {} has {} page views in the last 14 days'.format(package_dict['id'], pageviews_last_14_days))
                package_dict['pageviews_last_14_days'] = pageviews_last_14_days

            if _should_manually_load_property_value(context, package_dict, 'has_quickcharts'):
                package_dict['has_quickcharts'] = False
                for resource_dict in package_dict.get('resources', []):
                    resource_views = get_action('resource_view_list')(context, {'id': resource_dict['id']}) or []
                    for view in resource_views:
                        if view.get("view_type") == 'hdx_hxl_preview':
                            package_dict['has_quickcharts'] = True
                            break

            if _should_manually_load_property_value(context, package_dict, 'has_geodata'):
                package_dict['has_geodata'] = False
                for resource_dict in package_dict.get('resources', []):
                    if resource_dict.get('format') in GEODATA_FORMATS:
                        package_dict['has_geodata'] = True
                        break

            if _should_manually_load_property_value(context, package_dict, 'has_showcases'):
                package_dict['has_showcases'] = False
                package_dict['num_of_showcases'] = 0
                num_of_showcases = len(hdx_get_package_showcase_id_list(context, {'package_id': package_dict['id']}))
                if num_of_showcases > 0:
                    package_dict['has_showcases'] = True
                    package_dict['num_of_showcases'] = num_of_showcases

        dataset_dicts.append(package_dict)
    return dataset_dicts