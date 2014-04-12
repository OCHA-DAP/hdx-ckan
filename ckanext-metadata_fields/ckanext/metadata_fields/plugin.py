'''
Created on Apr 10, 2014

@author:alexandru-m-g
'''
import logging

import ckan.plugins as plugins
import ckan.plugins.toolkit as tk

import ckanext.metadata_fields.custom_validator as vd


class HdxMetadataFieldsPlugin(plugins.SingletonPlugin, tk.DefaultDatasetForm):
    plugins.implements(plugins.IConfigurer, inherit=False)
    plugins.implements(plugins.IDatasetForm, inherit=False)

    def update_config(self, config):
        tk.add_template_directory(config, 'templates')
        
    def is_fallback(self):
        return True

    def package_types(self):
        # default - no specific package type
        return []

    def _modify_package_schema(self, schema):
        
        schema.update({
                'package_creator': [tk.get_validator('not_empty'),
                    tk.get_converter('convert_to_extras')]
                })
        schema.update({
                'groups_list': [vd.groups_not_empty]
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
            'package_creator': [tk.get_converter('convert_from_extras'),
                tk.get_validator('ignore_missing')]
            })
        return schema
        
    def edit(self, entity):
        logging.warn("blabla");
        pass



