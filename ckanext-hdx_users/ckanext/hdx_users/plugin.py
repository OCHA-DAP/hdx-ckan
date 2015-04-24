import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import logging
import ckanext.hdx_users.actions.create as create
import ckanext.hdx_users.actions.get as get
import ckanext.hdx_users.actions.update as update


def user_create(context, data_dict=None):
    #Disable registering new users
    return {'success': False, 'msg': 'Registering is disabled at the moment!'}

class HDXUsersPlugin(plugins.SingletonPlugin):
    #plugins.implements(plugins.IAuthenticator)
    plugins.implements(plugins.IConfigurer, inherit=False)
    plugins.implements(plugins.IRoutes, inherit=True)
    plugins.implements(plugins.IActions)

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
        map.connect('/user/validate/{token}',
                    controller='ckanext.hdx_users.controllers.registration_controller:RequestController',
                    action='validate')
        map.connect('/user/post_register',
                    controller='ckanext.hdx_users.controllers.registration_controller:RequestController', action="post_register")
        map.connect('/user/validation_resend/{id}',
                    controller='ckanext.hdx_users.controllers.registration_controller:RequestController', action="validation_resend")
        map.connect('/user/logged_in', controller='ckanext.hdx_users.controllers.login_controller:LoginController', action='logged_in')
        map.connect('/user/reset', controller='ckanext.hdx_users.controllers.login_controller:LoginController', action='request_reset')
        map.connect('/contribute', controller='ckanext.hdx_users.controllers.login_controller:LoginController', action='contribute')

        return map
    
    def after_map(self, map):
        map.connect('user_dashboard', '/dashboard', controller='ckanext.hdx_users.controllers.dashboard_controller:DashboardController', action='dashboard',
                  ckan_icon='list')
        map.connect('user_dashboard_datasets', '/dashboard/datasets', controller='ckanext.hdx_users.controllers.dashboard_controller:DashboardController', action='dashboard_datasets',
                  ckan_icon='sitemap')
        return map

    def get_actions(self):
        return {
            'token_create': create.token_create,
            'token_show': get.token_show,
            'token_update': update.token_update
        }

    # def identify(self):
    #     token= logic.get_actions('token_show')(context, data_dict)
    #     return {'success': True}

    # def login(self):
    #     return True

    # def logout(self):
    #     return True


