import logging
import ckan.plugins as plugins
import ckan.plugins.toolkit as tk
import ckan.lib.plugins as lib_plugins

class HDXOrgFormPlugin(plugins.SingletonPlugin, lib_plugins.DefaultGroupForm):
    plugins.implements(plugins.IConfigurer, inherit=False)
    plugins.implements(plugins.IGroupForm, inherit=False)
    plugins.implements(plugins.ITemplateHelpers, inherit=False)

    num_times_new_template_called = 0
    num_times_read_template_called = 0
    num_times_edit_template_called = 0
    num_times_search_template_called = 0
    num_times_history_template_called = 0
    num_times_package_form_called = 0
    num_times_check_data_dict_called = 0
    num_times_setup_template_variables_called = 0

    def update_config(self, config):
        tk.add_template_directory(config, 'templates')

    def get_helpers(self):
        return {}

    def is_fallback(self):
        return False

    def group_types(self):
        return ['organization']

    def _modify_group_schema(self, schema):
        schema.update({
                'description':[tk.get_validator('not_empty')],
                'org_url':[tk.get_validator('not_missing'), tk.get_converter('convert_to_extras')],
                })
        return schema

    def form_to_db_schema(self):
        schema = super(HDXOrgFormPlugin, self).form_to_db_schema()
        schema = self._modify_group_schema(schema)
        return schema
        
#     def check_data_dict(self, data_dict):
#         return super(HDXOrgFormPlugin, self).check_data_dict(self, data_dict)
    
    def db_to_form_schema(self):
        # There's a bug in dictionary validation when form isn't present
        if tk.request.urlvars['action'] == 'index' or tk.request.urlvars['action'] == 'edit' or tk.request.urlvars['action'] == 'new':
            schema = super(HDXOrgFormPlugin, self).form_to_db_schema()
            schema.update({'description':[tk.get_validator('not_empty')] })
            schema.update({'org_url':[tk.get_validator('not_missing'), tk.get_converter('convert_to_extras')]})
            return schema
        else:
            return None
