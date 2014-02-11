import logging
import ckan.plugins as plugins
import ckan.plugins.toolkit as tk
import ckan.lib.plugins as lib_plugins

class UNIGroupFormPlugin(plugins.SingletonPlugin, lib_plugins.DefaultGroupForm):
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
		return {'language_code':'en'}

	def is_fallback(self):
		return True

	def group_types(self):
		return []

	def _modify_group_schema(self, schema):
		schema.update({'language_code':[tk.get_validator('ignore_missing'), tk.get_converter('convert_to_extras')]})
		return schema

	def create_group_schema(self):
		schema = super(UNIGroupFormPlugin, self).create_group_schema()
		schema = self._modify_group_schema(schema)
		return schema

	def update_group_schema(self):
		schema = super(UNIGroupFormPlugin, self).update_group_schema()
		schema = self._modify_group_schema(schema)
		return schema

	def show_group_schema(self):
		schema = super(UNIGroupFormPlugin, self).show_group_schema()
		schema.update({
			'language_code': [
			tk.get_converter('convert_from_extras'),
			tk.get_validator('ignore_missing')]
	})
		return schema


