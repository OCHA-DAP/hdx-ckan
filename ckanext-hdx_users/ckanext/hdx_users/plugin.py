import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import logging


def user_create(context, data_dict=None):
    #Disable registering new users
    return {'success': False, 'msg': 'Registering is disabled at the moment!'}

class HDXUsersPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer, inherit=False)
    plugins.implements(plugins.IRoutes, inherit=True)

    def update_config(self, config):
        toolkit.add_template_directory(config, 'templates')
    
    def get_helpers(self):
        return {}

    def is_fallback(self):
        return False

    def before_map(self, map):
        map.connect('user_dashboard', '/dashboard', controller='ckanext.hdx_users.controllers.dashboard_controller:DashboardController', action='dashboard',
                  ckan_icon='list')
        map.connect('user_dashboard_datasets', '/dashboard/datasets', controller='ckanext.hdx_users.controllers.dashboard_controller:DashboardController', action='dashboard_datasets',
                  ckan_icon='sitemap')
        map.connect('/user/register',
                    controller='ckanext.hdx_users.controllers.registration_controller:RequestController',
                    action='register')
        map.connect('/user/logged_in', controller='ckanext.hdx_users.controllers.login_controller:LoginController', action='logged_in')
        map.connect('/contribute', controller='ckanext.hdx_users.controllers.login_controller:LoginController', action='contribute')

        return map
    
    def after_map(self, map):
        map.connect('user_dashboard', '/dashboard', controller='ckanext.hdx_users.controllers.dashboard_controller:DashboardController', action='dashboard',
                  ckan_icon='list')
        map.connect('user_dashboard_datasets', '/dashboard/datasets', controller='ckanext.hdx_users.controllers.dashboard_controller:DashboardController', action='dashboard_datasets',
                  ckan_icon='sitemap')
        return map


