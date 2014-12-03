import logging, re
import ckan.plugins as plugins
import ckan.plugins.toolkit as tk
import ckan.lib.plugins as lib_plugins

def convert_country(q):
    for c in tk.get_action('group_list')({'user':'127.0.0.1'},{'all_fields': True}):
        if re.findall(c['display_name'].lower(),q.lower()):
            q += ' '+c['name']
    return q

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
        map.connect('simple_search',
            '/dataset', controller='ckanext.hdx_search.controllers.simple_search_controller:HDXSimpleSearchController', action='package_search')
        return map

    def after_map(self, map):
        map.connect('search', '/search',
                    controller='ckanext.hdx_search.controllers.search_controller:HDXSearchController', action='search')
        map.connect('simple_search',
            '/dataset', controller='ckanext.hdx_search.controllers.simple_search_controller:HDXSimpleSearchController', action='package_search')
        return map

    def before_search(self, search_params):
        if 'sort' in search_params:
            parts = search_params['sort'].split(' ')
            try:
                parts[1]
            except:
                search_params['sort'] = parts[0]+' desc'
        #search_params['q'] = convert_country(search_params['q'])
        if 'facet.field' in search_params and 'vocab_Topics' not in search_params['facet.field']:
            search_params['facet.field'].append('vocab_Topics')

        # If indicator flag is set, search only that type
        if 'ext_indicator' in search_params['extras']:
            if int(search_params['extras']['ext_indicator']) == 1:
                search_params['fq'] = search_params['fq'] + ' +extras_indicator:1'
            elif int(search_params['extras']['ext_indicator']) == 0:
                search_params['fq'] = search_params[
                    'fq'] + ' -extras_indicator:1'
        return search_params

    def after_search(self, search_results, search_params):
        return search_results

    def before_view(self, pkg_dict):
        return pkg_dict
