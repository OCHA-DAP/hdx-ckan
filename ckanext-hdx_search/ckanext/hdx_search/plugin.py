import logging
import ckan.plugins as plugins
import ckan.plugins.toolkit as tk
import ckan.lib.plugins as lib_plugins

class HDXSearchPlugin(plugins.SingletonPlugin):
	plugins.implements(plugins.IConfigurer, inherit=False)
	plugins.implements(plugins.IRoutes, inherit=True)
	plugins.implements(plugins.ITemplateHelpers, inherit=False)

	def update_config(self, config):
		tk.add_template_directory(config, 'templates')

	def get_helpers(self):
		return {}

	def before_map(self, map):
		map.connect('/search', controller='ckanext.hdx_search.controllers.search_controller:HDXSearchController', action='search')
		map.connect('/dataset', controller='ckanext.hdx_search.controllers.search_controller:HDXSearchController', action='package_search')
		return map


