import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit



class HDXThemePlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IRoutes, inherit=True)
    plugins.implements(plugins.ITemplateHelpers)

    def update_config(self, config):
        toolkit.add_template_directory(config, 'templates')
        toolkit.add_public_directory(config, 'public')
        toolkit.add_resource('fanstatic', 'hdx_theme')

    def before_map(self, map):
        map.connect('home', '/', controller='ckanext.hdx_theme.splash_page:SplashPageController', action='index')
        map.connect('/count/dataset', controller='ckanext.hdx_theme.count:CountController', action='dataset')
        map.connect('/count/country', controller='ckanext.hdx_theme.count:CountController', action='country')
        map.connect('/count/source', controller='ckanext.hdx_theme.count:CountController', action='source')
        map.connect('/contribute', controller='ckanext.hdx_theme.login:LoginController', action='contribute')
        return map

    def get_helpers(self):
        from ckanext.hdx_theme import helpers as hdx_helpers
        return {
            'is_downloadable': hdx_helpers.is_downloadable,
            'get_facet_items_dict':hdx_helpers.get_facet_items_dict,
            'get_last_modifier_user': hdx_helpers.get_last_modifier_user,
            'get_filtered_params_list':hdx_helpers.get_filtered_params_list
        }

