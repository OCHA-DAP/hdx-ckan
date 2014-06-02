'''
Created on Apr 10, 2014

@author:alexandru-m-g
'''
import logging

import ckan.plugins as plugins
import ckan.plugins.toolkit as tk
from routes.mapper import SubMapper

import ckanext.metadata_fields.custom_validator as vd
import ckanext.metadata_fields.update as update

def cached_group_list():
    return tk.get_action('cached_group_list')()


class HdxMetadataFieldsPlugin(plugins.SingletonPlugin, tk.DefaultDatasetForm):
    plugins.implements(plugins.IConfigurer, inherit=False)
    plugins.implements(plugins.IRoutes, inherit=True)
    plugins.implements(plugins.IDatasetForm, inherit=False)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IActions)

    def update_config(self, config):
        tk.add_template_directory(config, 'templates')

    def before_map(self, map):
        with SubMapper(map, controller='ckanext.metadata_fields.dataset_controller:DatasetController') as m:
            m.connect('add dataset', '/dataset/new', action='new')
            m.connect('/dataset/{action}/{id}',
                  requirements=dict(action='|'.join([
                      'new_metadata',
                      'new_resource',
                      ])))
        return map
        
    def is_fallback(self):
        return True

    def package_types(self):
        # default - no specific package type
        return []

    def _modify_package_schema(self, schema):
        
        schema.update({
                'notes': [tk.get_validator('not_empty')], #Notes == description. Makes description required
                'package_creator': [tk.get_validator('not_empty'),
                    tk.get_converter('convert_to_extras')],
                'groups_list': [vd.groups_not_empty],
            'caveats' : [tk.get_validator('ignore_missing'),
                    tk.get_converter('convert_to_extras')],
            'dataset_source' : [tk.get_validator('not_empty'),
                    tk.get_converter('convert_to_extras')],
            'dataset_date' : [tk.get_validator('ignore_missing'),
                    tk.get_converter('convert_to_extras')],
            'methodology' : [tk.get_validator('ignore_missing'),
                    tk.get_converter('convert_to_extras')],
            })

        return schema


    def create_package_schema(self):
        schema = super(HdxMetadataFieldsPlugin, self).create_package_schema()
        schema = self._modify_package_schema(schema)
        return schema

    def update_package_schema(self):
        schema = super(HdxMetadataFieldsPlugin, self).update_package_schema()
        schema = self._modify_package_schema(schema)
        return schema

    def show_package_schema(self):
        schema = super(HdxMetadataFieldsPlugin, self).show_package_schema()
        schema.update({
            'notes': [tk.get_validator('not_empty')], #Notes == description. Makes description required
            'package_creator': [tk.get_converter('convert_from_extras'),
                tk.get_validator('ignore_missing')],
            'caveats' : [tk.get_converter('convert_from_extras'),
                tk.get_validator('ignore_missing')],
            'dataset_source' : [tk.get_converter('convert_from_extras'),
                tk.get_validator('ignore_missing')],
            'dataset_date' : [tk.get_converter('convert_from_extras'),
                tk.get_validator('ignore_missing')],
            'methodology' : [tk.get_converter('convert_from_extras'),
                tk.get_validator('ignore_missing')],
            })
        return schema
    
    
    def get_helpers(self):
        return {'list_of_all_groups': cached_group_list}
    
    def get_actions(self):
        return {'package_update': update.package_update}
        


