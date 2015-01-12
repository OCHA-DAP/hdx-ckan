'''
Created on Apr 10, 2014

@author:alexandru-m-g
'''
import logging

import ckan.plugins as plugins
import ckan.plugins.toolkit as tk
from routes.mapper import SubMapper
import pylons.config as config
import ckan.model.package as package
import ckan.model.license as license
import ckanext.hdx_package.helpers.licenses as hdx_licenses
import ckanext.hdx_package.helpers.caching as caching


import ckanext.hdx_package.helpers.custom_validator as vd
import ckanext.hdx_package.helpers.update as update
import ckanext.hdx_package.actions.authorize as authorize
import ckanext.hdx_package.helpers.helpers as hdx_helpers


def run_on_startup():
    cache_on_startup = config.get('hdx.cache.onstartup', 'true')
    if 'true' == cache_on_startup:
        _generate_license_list()
        caching.cached_get_group_package_stuff()


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

    def update_config(self, config):
        tk.add_template_directory(config, 'templates')

    def before_map(self, map):
        map.connect('storage_file', '/storage/f/{label:.*}', controller='ckanext.hdx_package.controllers.storage_controller:FileDownloadController',
                    action='file')
        map.connect('perma_storage_file', '/dataset/{id}/resource_download/{resource_id}', controller='ckanext.hdx_package.controllers.storage_controller:FileDownloadController',
                    action='perma_file')
        map.connect('dataset_preselect', '/dataset/preselect',
                    controller='ckanext.hdx_package.controllers.dataset_controller:DatasetController', action='preselect')
        map.connect('resource_edit', '/dataset/{id}/resource_edit/{resource_id}',
                    controller='ckanext.hdx_package.controllers.dataset_controller:DatasetController', action='resource_edit', ckan_icon='edit')
        map.connect('shorten_url', '/package/tools/shorten',
                    controller='ckanext.hdx_package.controllers.dataset_controller:DatasetController', action='shorten')

        with SubMapper(map, controller='ckanext.hdx_package.controllers.dataset_controller:DatasetController') as m:
            m.connect('add dataset', '/dataset/new', action='new')
            m.connect(
                '/dataset/{id}/resource_delete/{resource_id}', action='resource_delete')
            m.connect('/dataset/{id}.{format}', action='read')
            m.connect('dataset_read', '/dataset/{id}', action='read',
                      ckan_icon='sitemap')
            m.connect('/dataset/{action}/{id}',
                      requirements=dict(action='|'.join([
                          'new_metadata',
                          'new_resource',
                          'visibility',
                      ])))

        map.connect(
            '/indicator/{id}', controller='ckanext.hdx_package.controllers.indicator:IndicatorController', action='read')
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
            'package_creator': [tk.get_validator('not_empty'),
                                tk.get_converter('convert_to_extras')],
            'groups_list': [vd.groups_not_empty],
            'indicator': [tk.get_validator('ignore_missing'),
                          tk.get_converter('convert_to_extras')],
            'last_data_update_date': [tk.get_validator('ignore_missing'),
                                      tk.get_converter('convert_to_extras')],
            'last_metadata_update_date': [tk.get_validator('ignore_missing'),
                                          tk.get_converter('convert_to_extras')],
            'dataset_source_code': [tk.get_validator('ignore_missing'),
                                    tk.get_converter('convert_to_extras')],
            'indicator_type': [tk.get_validator('ignore_missing'),
                               tk.get_converter('convert_to_extras')],
            'indicator_type_code': [tk.get_validator('ignore_missing'),
                                    tk.get_converter('convert_to_extras')],
            'dataset_summary': [tk.get_validator('ignore_missing'),
                                tk.get_converter('convert_to_extras')],
            'methodology': [tk.get_validator('ignore_missing'),
                            tk.get_converter('convert_to_extras')],
            'more_info': [tk.get_validator('ignore_missing'),
                          tk.get_converter('convert_to_extras')],
            'terms_of_use': [tk.get_validator('ignore_missing'),
                             tk.get_converter('convert_to_extras')],
            'validation_notes_and_comments': [tk.get_validator('ignore_missing'),
                                              tk.get_converter('convert_to_extras')],
            'caveats': [tk.get_validator('ignore_missing'),
                        tk.get_converter('convert_to_extras')],
            'dataset_source': [tk.get_validator('not_empty'),
                               tk.get_converter('convert_to_extras')],
            'dataset_date': [tk.get_validator('ignore_missing'),
                             tk.get_converter('convert_to_extras')],
            'methodology': [tk.get_validator('ignore_missing'),
                            tk.get_converter('convert_to_extras')],
            'methodology_other': [tk.get_validator('ignore_missing'),
                                  tk.get_converter('convert_to_extras')],
            'license_other': [tk.get_validator('ignore_missing'),
                              tk.get_converter('convert_to_extras')],
        })

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
            'dataset_source_code': [tk.get_converter('convert_from_extras'),
                                    tk.get_validator('ignore_missing')],
            'indicator_type': [tk.get_converter('convert_from_extras'),
                               tk.get_validator('ignore_missing')],
            'indicator_type_code': [tk.get_converter('convert_from_extras'),
                                    tk.get_validator('ignore_missing')],
            'dataset_summary': [tk.get_converter('convert_from_extras'),
                                tk.get_validator('ignore_missing')],
            'methodology': [tk.get_converter('convert_from_extras'),
                            tk.get_validator('ignore_missing')],
            'more_info': [tk.get_converter('convert_from_extras'),
                          tk.get_validator('ignore_missing')],
            'terms_of_use': [tk.get_converter('convert_from_extras'),
                             tk.get_validator('ignore_missing')],
            'validation_notes_and_comments': [tk.get_converter('convert_from_extras'),
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
        })
        return schema

    def get_helpers(self):
        return {'list_of_all_groups': cached_group_list,
                'hdx_find_license_name': hdx_helpers.hdx_find_license_name}

    def get_actions(self):
        from ckanext.hdx_package.helpers import helpers as hdx_actions
        return {
            'package_update': update.package_update,
            'hdx_get_activity_list': hdx_actions.hdx_get_activity_list,
            'hdx_package_update_metadata': update.hdx_package_update_metadata,
            'hdx_resource_update_metadata': update.hdx_resource_update_metadata,
            'tag_autocomplete': hdx_actions.hdx_tag_autocomplete_list,
            'package_create': hdx_actions.package_create
        }

    def get_auth_functions(self):
        return {'package_create': authorize.package_create,
                'package_update': authorize.package_update}

    def make_middleware(self, app, config):
        run_on_startup()
        return app
