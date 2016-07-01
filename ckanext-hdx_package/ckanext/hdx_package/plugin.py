'''
Created on Apr 10, 2014

@author:alexandru-m-g
'''
import logging
from routes.mapper import SubMapper
import pylons.config as config
import json
import ijson
import io

import ckan.plugins as plugins
import ckan.plugins.toolkit as tk
import ckan.plugins as p
import ckan.plugins.toolkit as toolkit
import ckan.model as model
import ckan.model.package as package
import ckan.model.license as license
import ckan.logic as logic

import ckanext.resourceproxy.plugin as resourceproxy_plugin

import ckanext.hdx_package.helpers.licenses as hdx_licenses
import ckanext.hdx_package.helpers.caching as caching
import ckanext.hdx_package.helpers.custom_validator as vd
import ckanext.hdx_package.helpers.update as update
import ckanext.hdx_package.actions.authorize as authorize
import ckanext.hdx_package.actions.create as hdx_create
import ckanext.hdx_package.actions.update as hdx_update
import ckanext.hdx_package.actions.delete as hdx_delete
import ckanext.hdx_package.helpers.helpers as hdx_helpers
import ckanext.hdx_package.helpers.tracking_changes as tracking_changes
import ckanext.hdx_package.helpers.analytics as analytics
import ckanext.hdx_package.actions.get as hdx_get

import ckanext.hdx_org_group.helpers.organization_helper as org_helper

from ckan.lib import uploader

log = logging.getLogger(__name__)

ignore_empty = p.toolkit.get_validator('ignore_empty')


def run_on_startup():
    cache_on_startup = config.get('hdx.cache.onstartup', 'true')
    if 'true' == cache_on_startup:
        _generate_license_list()
        caching.cached_get_group_package_stuff()

    compile_less_on_startup = config.get('hdx.less_compile.onstartup', 'false')
    if 'true' == compile_less_on_startup:
        org_helper.recompile_everything({'model': model, 'session': model.Session,
                   'user': 'hdx', 'ignore_auth': True})

    # replace original get_proxified_resource_url, check hdx_get_proxified_resource_url for more info
    resourceproxy_plugin.get_proxified_resource_url = hdx_helpers.hdx_get_proxified_resource_url

    # wrap resource download function so that we can track download events
    analytics.wrap_resource_download_function()


def _generate_license_list():
    package.Package._license_register = license.LicenseRegister()
    package.Package._license_register.licenses = [
        license.License(
            hdx_licenses.LicenseCreativeCommonsIntergovernmentalOrgs()),
        license.License(license.LicenseCreativeCommonsAttribution()),
        license.License(license.LicenseCreativeCommonsAttributionShareAlike()),
        license.License(hdx_licenses.LicenseHdxOpenDatabaseLicense()),
        license.License(
            hdx_licenses.LicenseHdxOpenDataCommonsAttributionLicense()),
        license.License(
            hdx_licenses.LicenseHdxOpenDataCommonsPublicdomainDedicationAndLicense()),
        license.License(hdx_licenses.LicenseOtherPublicDomainNoRestrictions()),
        license.License(hdx_licenses.LicenseHdxMultiple()),
        license.License(hdx_licenses.LicenseHdxOther())
    ]


def cached_group_list():
    return tk.get_action('cached_group_list')()


class HDXPackagePlugin(plugins.SingletonPlugin, tk.DefaultDatasetForm):
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.IConfigurer, inherit=False)
    plugins.implements(plugins.IRoutes, inherit=True)
    plugins.implements(plugins.IDatasetForm, inherit=False)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IMiddleware, inherit=True)
    plugins.implements(plugins.IResourceController, inherit=True)
    plugins.implements(plugins.IValidators, inherit=True)

    def update_config(self, config):
        tk.add_template_directory(config, 'templates')

    def after_map(self, map):
        map.connect('dataset_edit', '/dataset/edit/{id}',
                    controller='ckanext.hdx_package.controllers.dataset_old_links_controller:DatasetOldLinks',
                    action='show_notification_page')

        return map

    def before_map(self, map):
        map.connect('storage_file', '/storage/f/{label:.*}', controller='ckanext.hdx_package.controllers.storage_controller:FileDownloadController',
                    action='file')
        map.connect('perma_storage_file', '/dataset/{id}/resource_download/{resource_id}', controller='ckanext.hdx_package.controllers.dataset_controller:DatasetController',
                    action='resource_download')
        map.connect('dataset_preselect', '/dataset/preselect',
                    controller='ckanext.hdx_package.controllers.dataset_controller:DatasetController', action='preselect')
        # map.connect('resource_edit', '/dataset/{id}/resource_edit/{resource_id}',
        #             controller='ckanext.hdx_package.controllers.dataset_controller:DatasetController', action='resource_edit', ckan_icon='edit')
        map.connect('resource_read', '/dataset/{id}/resource/{resource_id}',
                    controller='ckanext.hdx_package.controllers.dataset_controller:DatasetController', action='resource_read')
        map.connect('shorten_url', '/package/tools/shorten',
                    controller='ckanext.hdx_package.controllers.dataset_controller:DatasetController', action='shorten')
        map.connect('resource_datapreview', '/dataset/{id}/resource/{resource_id}/preview',
                    controller='ckanext.hdx_package.controllers.dataset_controller:DatasetController', action='resource_datapreview')
        map.connect('related_edit', '/dataset/{id}/related/edit/{related_id}', controller='ckanext.hdx_package.controllers.related_controller:RelatedController',
                  action='edit')

        map.connect('add dataset', '/dataset/new',
                    controller='ckanext.hdx_package.controllers.dataset_old_links_controller:DatasetOldLinks',
                    action='new_notification_page')
        map.connect('dataset_edit', '/dataset/edit/{id}',
                    controller='ckanext.hdx_package.controllers.dataset_old_links_controller:DatasetOldLinks',
                    action='edit_notification_page')
        map.connect('resource_edit', '/dataset/{id}/resource_edit/{resource_id}',
                    controller='ckanext.hdx_package.controllers.dataset_old_links_controller:DatasetOldLinks',
                    action='resource_edit_notification_page', ckan_icon='edit')
        map.connect('new_resource', '/dataset/new_resource/{id}',
                    controller='ckanext.hdx_package.controllers.dataset_old_links_controller:DatasetOldLinks',
                    action='resource_new_notification_page')
        map.connect('dataset_resources', '/dataset/resources/{id}',
                    controller='ckanext.hdx_package.controllers.dataset_old_links_controller:DatasetOldLinks',
                    action='resources_notification_page')
        with SubMapper(map, controller='ckanext.hdx_package.controllers.dataset_controller:DatasetController') as m:
            # m.connect('add dataset', '/dataset/new', action='new')
            m.connect(
                '/dataset/{id}/resource_delete/{resource_id}', action='resource_delete')
            m.connect('/dataset/{id}.{format}', action='read')
            m.connect('dataset_read', '/dataset/{id}', action='read',
                      ckan_icon='sitemap')
            m.connect('/dataset/{action}/{id}',
                      requirements=dict(action='|'.join([
                          'new_metadata',
                          # 'new_resource',
                          'visibility',
                          'delete',
                          # 'edit',
                      ])))

        map.connect(
            '/indicator/{id}', controller='ckanext.hdx_package.controllers.indicator:IndicatorController', action='read')

        #map.connect('/api/action/package_create', controller='ckanext.hdx_package.controllers.dataset_controller:HDXApiController', action='package_create', conditions=dict(method=['POST']))
        map.connect('/contribute/new',
                    controller='ckanext.hdx_package.controllers.contribute_flow_controller:ContributeFlowController',
                    action='new')
        map.connect('/contribute/edit/{id}',
                    controller='ckanext.hdx_package.controllers.contribute_flow_controller:ContributeFlowController',
                    action='edit')
        map.connect('/contribute/validate',
                    controller='ckanext.hdx_package.controllers.contribute_flow_controller:ContributeFlowController',
                    action='validate')

        return map

    def is_fallback(self):
        return True

    def package_types(self):
        # default - no specific package type
        return []

    def _modify_package_schema(self, schema):

        schema.update({
            # Notes == description. Makes description required
            'notes': [tk.get_validator('not_empty')],
            'package_creator': [ tk.get_validator('find_package_creator'),
                                tk.get_validator('not_empty'),
                                tk.get_converter('convert_to_extras')],
            'groups_list': [vd.groups_not_empty],
            'indicator': [tk.get_validator('ignore_missing'),
                          tk.get_converter('convert_to_extras')],
            'last_data_update_date': [tk.get_validator('ignore_missing'),
                                      tk.get_converter('convert_to_extras')],
            'last_metadata_update_date': [tk.get_validator('ignore_missing'),
                                          tk.get_converter('convert_to_extras')],
            'dataset_source_short_name': [tk.get_validator('ignore_missing'),
                                          tk.get_converter('convert_to_extras')],
            'indicator_type': [tk.get_validator('ignore_missing'),
                               tk.get_converter('convert_to_extras')],
            'indicator_type_code': [tk.get_validator('ignore_missing'),
                                    tk.get_converter('convert_to_extras')],
            'dataset_summary': [tk.get_validator('ignore_missing'),
                                tk.get_converter('convert_to_extras')],
            'more_info': [tk.get_validator('ignore_missing'),
                          tk.get_converter('convert_to_extras')],
            'terms_of_use': [tk.get_validator('ignore_missing'),
                             tk.get_converter('convert_to_extras')],
            'source_code': [tk.get_validator('ignore_missing'),
                            tk.get_converter('convert_to_extras')],
            'caveats': [tk.get_validator('ignore_missing'),
                        tk.get_converter('convert_to_extras')],
            'dataset_source': [tk.get_validator('not_empty'),
                               tk.get_converter('convert_to_extras')],
            'dataset_date': [tk.get_validator('not_empty'),
                             tk.get_converter('convert_to_extras')],
            'methodology': [tk.get_validator('not_empty'),
                            tk.get_converter('convert_to_extras')],
            'methodology_other': [tk.get_validator('not_empty_if_methodology_other'),
                                  tk.get_converter('convert_to_extras')],
            'license_id': [tk.get_validator('not_empty'), unicode],
            'license_other': [tk.get_validator('not_empty_if_license_other'),
                              tk.get_converter('convert_to_extras')],
            'solr_additions': [tk.get_validator('ignore_missing'),
                              tk.get_converter('convert_to_extras')],
            'subnational': [tk.get_validator('ignore_missing'),
                              tk.get_converter('convert_to_extras')],
            'quality': [tk.get_validator('ignore_not_sysadmin'), tk.get_validator('ignore_missing'),
                              tk.get_converter('convert_to_extras')],
            'data_update_frequency': [tk.get_validator('not_empty'),
                              tk.get_converter('convert_to_extras')]
        })

        schema['resources'].update(
            {
                'name': [tk.get_validator('not_empty'), unicode, tk.get_validator('remove_whitespace')],
                'format': [tk.get_validator('hdx_detect_format'), tk.get_validator('not_empty'),
                           tk.get_validator('clean_format'), unicode]
            }
        )

        return schema

    def create_package_schema(self):
        schema = super(HDXPackagePlugin, self).create_package_schema()
        schema = self._modify_package_schema(schema)
        return schema

    def update_package_schema(self):
        schema = super(HDXPackagePlugin, self).update_package_schema()
        schema = self._modify_package_schema(schema)
        return schema

    def show_package_schema(self):
        schema = super(HDXPackagePlugin, self).show_package_schema()
        schema.update({
            # Notes == description. Makes description required
            'notes': [tk.get_validator('not_empty')],
            'package_creator': [tk.get_converter('convert_from_extras'),
                                tk.get_validator('ignore_missing')],
            'indicator': [tk.get_converter('convert_from_extras'),
                          tk.get_validator('ignore_missing')],
            'last_data_update_date': [tk.get_converter('convert_from_extras'),
                                      tk.get_validator('ignore_missing')],
            'last_metadata_update_date': [tk.get_converter('convert_from_extras'),
                                          tk.get_validator('ignore_missing')],
            'dataset_source_short_name': [tk.get_converter('convert_from_extras'),
                                          tk.get_validator('ignore_missing')],
            'indicator_type': [tk.get_converter('convert_from_extras'),
                               tk.get_validator('ignore_missing')],
            'indicator_type_code': [tk.get_converter('convert_from_extras'),
                                    tk.get_validator('ignore_missing')],
            'dataset_summary': [tk.get_converter('convert_from_extras'),
                                tk.get_validator('ignore_missing')],
            'more_info': [tk.get_converter('convert_from_extras'),
                          tk.get_validator('ignore_missing')],
            'terms_of_use': [tk.get_converter('convert_from_extras'),
                             tk.get_validator('ignore_missing')],
            'source_code': [tk.get_converter('convert_from_extras'),
                            tk.get_validator('ignore_missing')],
            'caveats': [tk.get_converter('convert_from_extras'),
                        tk.get_validator('ignore_missing')],
            'dataset_source': [tk.get_converter('convert_from_extras'),
                               tk.get_validator('ignore_missing')],
            'dataset_date': [tk.get_converter('convert_from_extras'),
                             tk.get_validator('ignore_missing')],
            'methodology': [tk.get_converter('convert_from_extras'),
                            tk.get_validator('ignore_missing')],
            'methodology_other': [tk.get_converter('convert_from_extras'),
                                  tk.get_validator('ignore_missing')],
            'license_other': [tk.get_converter('convert_from_extras'),
                              tk.get_validator('ignore_missing')],
            'solr_additions': [tk.get_converter('convert_from_extras'),
                              tk.get_validator('ignore_missing')],
            'subnational': [tk.get_converter('convert_from_extras'),
                              tk.get_validator('ignore_missing')],
            'quality': [tk.get_converter('convert_from_extras'), tk.get_validator('ignore_missing')],
            'data_update_frequency': [tk.get_converter('convert_from_extras'),
                              tk.get_validator('ignore_missing')]
        })
        return schema

    def get_helpers(self):
        return {
            'list_of_all_groups': cached_group_list,
            'hdx_find_license_name': hdx_helpers.hdx_find_license_name,
            'filesize_format': hdx_helpers.filesize_format,
            'generate_mandatory_fields': hdx_helpers.generate_mandatory_fields,
            'hdx_check_add_data': hdx_helpers.hdx_check_add_data,
        }

    def get_actions(self):
        from ckanext.hdx_package.helpers import helpers as hdx_actions
        return {
            'package_update': update.package_update,
            'hdx_get_activity_list': hdx_actions.hdx_get_activity_list,
            'hdx_package_update_metadata': update.hdx_package_update_metadata,
            'hdx_resource_update_metadata': update.hdx_resource_update_metadata,
            'hdx_resource_delete_metadata': update.hdx_resource_delete_metadata,
            'hdx_resource_id_list': hdx_get.hdx_resource_id_list,
            'tag_autocomplete': hdx_actions.hdx_tag_autocomplete_list,
            'package_create': hdx_actions.package_create,
            'resource_create': hdx_create.resource_create,
            'resource_update': hdx_update.resource_update,
            'resource_show': hdx_get.resource_show,
            'package_purge': hdx_delete.hdx_dataset_purge,
            'package_search': hdx_get.package_search,
            'package_show': hdx_get.package_show,
            'package_show_edit': hdx_get.package_show_edit,
            'package_validate': hdx_get.package_validate
        }

    def before_show(self, resource_dict):
        '''
            This is run before a resource is displayed.
            We use it to show the correct tracking summary
        '''
        tracking_changes.add_tracking_summary_to_resource_dict(resource_dict)
        return resource_dict

    def get_validators(self):
        return {
            'hdx_detect_format': vd.detect_format,
            'find_package_creator': vd.find_package_creator,
            'not_empty_if_methodology_other': vd.general_not_empty_if_other_selected('methodology', 'Other'),
            'not_empty_if_license_other': vd.general_not_empty_if_other_selected('license_id', 'hdx-other')
        }

    def get_auth_functions(self):
        return {'package_create': authorize.package_create,
                'package_update': authorize.package_update,
                'hdx_resource_id_list': authorize.hdx_resource_id_list}

    def make_middleware(self, app, config):
        run_on_startup()
        return app

    def validate(self, context, data_dict, schema, action):
        '''
            We're using a different validation schema if the dataset is private !
        '''
        if action in ['package_create', 'package_update']:
            private = False if str(data_dict.get('private','')).lower() == 'false' else True

            if private:
                schema['notes'] = [tk.get_validator('ignore_missing'), unicode]
                schema['methodology'] = [tk.get_validator('ignore_missing'), tk.get_converter('convert_to_extras')]
                schema['dataset_date'] = [tk.get_validator('ignore_missing'), tk.get_converter('convert_to_extras')]
                schema['data_update_frequency'] = [tk.get_validator('ignore_missing'),
                                                   tk.get_converter('convert_to_extras')]

                if 'groups_list' in schema:
                    del schema['groups_list']

        return toolkit.navl_validate(data_dict, schema, context)


class HDXChartViewsPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IResourceView, inherit=True)

    def info(self):
        schema = {
            'chart_type': [],
            'x_axis_label': [ignore_empty],
            'y_axis_label': [],
            'x_column': [],
            'y_column': [],
            'chart_data_source': [],
            'data_link_url': [],
            'data_label': []
        }
        return {
            'name': 'hdx_chart_view',
            'title': 'Line / Bar Chart',
            'filterable': False,
            'preview_enabled': True,
            'icon': 'bar-chart',
            'requires_datastore': True,
            'iframed': True,
            'schema': schema,
            'default_title': p.toolkit._('HDX New Chart')
        }

    def can_view(self, data_dict):
        resource = data_dict['resource']
        return (resource.get('datastore_active') or
                resource.get('url') == '_datastore_only_resource')

    def setup_template_variables(self, context, data_dict):

        return {
            'datastore_columns': self._datastore_cols(data_dict['resource']),
            'chart_type': [
                {
                    'value': 'bar',
                    'text': p.toolkit._('Bar Chart')
                },
                {
                    'value': 'area',
                    'text': p.toolkit._('Line Area Chart')
                },
                {
                    'value': 'line',
                    'text': p.toolkit._('Line Chart')
                },
            ],
            'chart_info': self._format_settings_for_chart(data_dict['resource'], data_dict['resource_view'])
        }

    def view_template(self, context, data_dict):
        return 'new_views/chart_view.html'

    def form_template(self, context, data_dict):
        return 'new_views/chart_view_form.html'

    def _format_settings_for_chart(self, resource_dict, resource_view_dict):
        result = {
            'title': resource_view_dict.get('title'),
            'title_x': resource_view_dict.get('x_axis_label'),
            'title_y': resource_view_dict.get('y_axis_label'),
            'type': resource_view_dict.get('chart_type'),
            'sources': [
                {
                    'label_x': resource_view_dict.get('data_label'),
                    'column_x': resource_view_dict.get('x_column'),
                    'column_y': resource_view_dict.get('y_column'),
                    'data_link_url': resource_view_dict.get('data_link_url'),
                    'source': resource_view_dict.get('chart_data_source'),
                    'datastore_id': resource_dict.get('id'),
                    'source_type': 'ckan'
                }
            ]
        }
        return result

    def _datastore_cols(self, resource):
        '''
        Returns a list of columns found in this resource's datastore
        '''
        data = {'resource_id': resource['id'], 'limit': 0}
        fields = toolkit.get_action('datastore_search')({}, data)['fields']
        return [{'value': col['id'], 'text': col['id']} for col in fields if col != '_id']


class HDXGeopreviewPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IResourceView, inherit=True)

    def info(self):
        return {
            'name': 'hdx_geopreview_view',
            'title': 'Geopreview',
            'filterable': False,
            'preview_enabled': True,
            'requires_datastore': False,
            'iframed': True,
            'default_title': p.toolkit._('Geopreview')
        }

    def can_view(self, data_dict):
        from ckanext.hdx_package.helpers.geopreview import GIS_FORMATS

        resource = data_dict.get('resource', {})
        format = resource.get('format')
        format = format.lower() if format else ''
        return format in GIS_FORMATS

    def setup_template_variables(self, context, data_dict):
        from ckanext.hdx_package.controllers.dataset_controller import DatasetController

        shape_info = DatasetController._process_shapes([data_dict['resource']])

        return {
            'shape_info': json.dumps(shape_info)
        }

    def view_template(self, context, data_dict):
        return 'new_views/geopreview_view.html'

    def form_template(self, context, data_dict):
        return 'new_views/geopreview_view_form.html'


class HDXKeyFiguresPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IResourceView, inherit=True)

    def info(self):
        return {
            'name': 'hdx_key_figures_view',
            'title': 'Key Figures',
            'filterable': False,
            'preview_enabled': True,
            'requires_datastore': True,
            'iframed': True,
            'default_title': p.toolkit._('Key Figures')
        }

    def can_view(self, data_dict):
        resource = data_dict['resource']
        return (resource.get('datastore_active') or
                resource.get('url') == '_datastore_only_resource')

    def setup_template_variables(self, context, data_dict):
        import ckanext.hdx_crisis.dao.location_data_access as location_data_access
        id = data_dict['resource']['id']
        key_figures = location_data_access.get_formatted_topline_numbers(id)

        return {
            'key_figures': key_figures
        }

    def view_template(self, context, data_dict):
        return 'new_views/key_figures_view.html'

    def form_template(self, context, data_dict):
        return 'new_views/key_figures_view_form.html'


class HDXChoroplethMapPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IResourceView, inherit=True)

    def info(self):
        schema = {
            'map_name': [],
            'district_name_column': [],
            'values_resource_id': [],
            'values_column_name': [],
            'values_description_column': [],
            'map_join_column': [],
            'values_join_column': [],
            'threshold': [],
            'max_zoom': [],
            'show_legend': []
        }
        return {
            'name': 'hdx_choropleth_map_view',
            'title': 'Choropleth Map',
            'schema': schema,
            'filterable': False,
            'preview_enabled': True,
            'requires_datastore': False,
            'iframed': True,
            'default_title': p.toolkit._('Choropleth Map')
        }

    def can_view(self, data_dict):
        resource = data_dict.get('resource', {})
        format = resource.get('format')
        format = format.lower() if format else ''

        return format == 'geojson'

    def _detect_fields_in_geojson(self, resource_dict):
        geo_columns_dict = {}
        try:
            upload = uploader.ResourceUpload(resource_dict)
            with io.open(upload.get_path(resource_dict['id']), 'rb') as f, io.TextIOWrapper(f,
                                                                                            encoding='utf-8-sig') as tf:
                parser = ijson.parse(tf)

                geo_columns = set()
                i = 0
                for prefix, event, value in parser:
                    if prefix == u'features.item.properties' and event == u'map_key':
                        geo_columns.add(value)
                        i += 1

                    if i > 10:
                        break
                    pass
                geo_columns_dict = [{'value': item, 'text': item} for item in sorted(geo_columns)]
        except Exception as e:
            log.warn(u'Error accessing resource size for resource {}: {}'.format(resource_dict.get('name', ''),
                                                                                 str(e)))
            geo_columns_dict = {}
        return geo_columns_dict

    def setup_template_variables(self, context, data_dict):

        max_zoom_values = [{'value': str(item), 'text': str(item)} for item in range(1, 16)]
        max_zoom_values.insert(0, {'value': 'default', 'text': p.toolkit._('Default')})

        show_legend_values = [
            {
                'value': 'true',
                'text': p.toolkit._('Yes')
            },
            {
                'value': 'false',
                'text': p.toolkit._('No')
            }
        ]

        geo_columns_dict = self._detect_fields_in_geojson(data_dict['resource'])

        resource_view_dict = data_dict['resource_view']

        values_resource_id = resource_view_dict.get('values_resource_id')
        if values_resource_id:

            values_res_dict = logic.get_action('resource_show')(context, {'id': values_resource_id})

            return {
                'map': {
                    'map_datatype_2': 'filestore',
                    'map_district_name_column': resource_view_dict.get('district_name_column'),
                    'map_datatype_1': 'datastore',
                    'map_dataset_id_1': values_res_dict.get('package_id'),
                    'map_dataset_id_2': data_dict['resource'].get('package_id'),
                    'map_resource_id_2': data_dict['resource'].get('id'),
                    'map_resource_id_1': values_resource_id,
                    'map_title': resource_view_dict.get('map_name'),
                    'map_values': resource_view_dict.get('values_column_name'),
                    'map_column_2': resource_view_dict.get('map_join_column'),
                    'map_column_1': resource_view_dict.get('values_join_column'),
                    'map_description_column': resource_view_dict.get('values_description_column'),
                    'is_crisis': 'false',
                    'basemap_url': 'default',
                    'map_threshold': resource_view_dict.get('threshold'),
                    'max_zoom': resource_view_dict.get('max_zoom'),
                    'show_legend': resource_view_dict.get('show_legend'),
                },
                'formdata': {
                    'map_columns': geo_columns_dict,
                    'max_zoom_values': max_zoom_values,
                    'show_legend_values': show_legend_values
                }

            }
        else:
            return {
                'formdata': {
                    'map_columns': geo_columns_dict,
                    'max_zoom_values': max_zoom_values,
                    'show_legend_values': show_legend_values
                }
            }

    def view_template(self, context, data_dict):
        return 'new_views/choropleth_map_view.html'

    def form_template(self, context, data_dict):
        return 'new_views/choropleth_map_view_form.html'
