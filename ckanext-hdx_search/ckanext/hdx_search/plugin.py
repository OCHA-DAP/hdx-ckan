import logging
import ckan.plugins as plugins
import ckan.plugins.toolkit as tk
import ckan.lib.plugins as lib_plugins


class HDXSearchPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer, inherit=False)
    plugins.implements(plugins.IRoutes, inherit=True)
    plugins.implements(plugins.ITemplateHelpers, inherit=False)
    plugins.implements(plugins.IPackageController, inherit=True)

    def update_config(self, config):
        tk.add_template_directory(config, 'templates')

    def get_helpers(self):
        return {}

    def before_map(self, map):
        map.connect('search', '/search',
                    controller='ckanext.hdx_search.controllers.search_controller:HDXSearchController', action='search')
        map.connect(
            '/dataset', controller='ckanext.hdx_search.controllers.search_controller:HDXSearchController', action='package_search')
        return map

    def after_map(self, map):
        map.connect('search', '/search',
                    controller='ckanext.hdx_search.controllers.search_controller:HDXSearchController', action='search')
        map.connect(
            '/dataset', controller='ckanext.hdx_search.controllers.search_controller:HDXSearchController', action='package_search')
        return map

    def before_search(self, search_params):
        # If indicator flag is set, search only that type
        if 'ext_indicator' in search_params['extras']:
            if int(search_params['extras']['ext_indicator']) == 1:
                search_params['q'] = search_params['q'] + '+extras_indicator:1'
            elif int(search_params['extras']['ext_indicator']) == 0:
                search_params['q'] = search_params[
                    'q'] + '-extras_indicator:1'
        return search_params

    def after_search(self, search_results, search_params):
        return search_results

    def before_view(self, pkg_dict):
        return pkg_dict
