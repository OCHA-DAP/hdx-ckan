import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import logging
import ckanext.hdx_users.actions.create as create
import ckanext.hdx_users.actions.get as get
import ckanext.hdx_users.actions.update as update


def user_create(context, data_dict=None):
    #Disable registering new users
    return {'success': False, 'msg': 'Registering is disabled at the moment!'}

class HDXValidatePlugin(plugins.SingletonPlugin):
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
        map.connect('/user/register',
                    controller='ckanext.hdx_users.controllers.mail_validation_controller:ValidationController',
                    action='register')
        map.connect('/user/validate/{token}',
                    controller='ckanext.hdx_users.controllers.mail_validation_controller:ValidationController',
                    action='validate')
        map.connect('/user/post_register',
                    controller='ckanext.hdx_users.controllers.mail_validation_controller:ValidationController', action="post_register")
        map.connect('/user/validation_resend/{id}',
                    controller='ckanext.hdx_users.controllers.mail_validation_controller:ValidationController', action="validation_resend")
        map.connect('/user/logged_in', controller='ckanext.hdx_users.controllers.mail_validation_controller:ValidationController', action='logged_in')
        
        return map
    
    def after_map(self, map):
        return map

    def get_actions(self):
        return {
            'token_create': create.token_create,
            'token_show': get.token_show,
            'token_update': update.token_update
        }


class HDXUsersPlugin(plugins.SingletonPlugin):
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
        map.connect('/user/logged_in', controller='ckanext.hdx_users.controllers.login_controller:LoginController', action='logged_in')
        map.connect('/user/reset', controller='ckanext.hdx_users.controllers.login_controller:LoginController', action='request_reset')
        map.connect('/contribute', controller='ckanext.hdx_users.controllers.login_controller:LoginController', action='contribute')
        ## Included to fix fussiness when overriding user profile route
        map.connect('/user/edit', controller='user', action='edit')
        map.connect('/user/activity/{id}/{offset}', controller='user', action='activity')
        map.connect('user_activity_stream', '/user/activity/{id}',
                   controller='user', action='activity', ckan_icon='time')
        map.connect('user_follow', '/user/follow/{id}',  controller='user', action='follow')
        map.connect('/user/unfollow/{id}',  controller='user', action='unfollow')
        map.connect('user_followers', '/user/followers/{id:.*}',
                   controller='user', action='followers', ckan_icon='group')
        map.connect('user_edit', '/user/edit/{id:.*}',  controller='user', action='edit',
                  ckan_icon='cog')
        map.connect('user_delete', '/user/delete/{id}',  controller='user', action='delete')
        map.connect('register', '/user/register', controller='user', action='register')
        map.connect('login', '/user/login', controller='user', action='login')
        map.connect('/user/_logout', controller='user', action='logout')
        map.connect('/user/logged_in', controller='user', action='logged_in')
        map.connect('/user/logged_out', controller='user', action='logged_out')
        map.connect('/user/logged_out_redirect', controller='user', action='logged_out_page')
        map.connect('/user/reset', controller='user', action='request_reset')
        map.connect('/user/me', controller='user', action='me')
        map.connect('/user/reset/{id:.*}',  controller='user', action='perform_reset')
        map.connect('/user/set_lang/{lang}',  controller='user', action='set_lang')
        #######
        map.connect('user_datasets', '/user/{id:.*}',  controller='ckanext.hdx_users.controllers.dashboard_controller:DashboardController', action='read', ckan_icon='sitemap')
        return map
    
    def after_map(self, map):
        map.connect('user_dashboard', '/dashboard', controller='ckanext.hdx_users.controllers.dashboard_controller:DashboardController', action='dashboard',
                  ckan_icon='list')
        map.connect('user_dashboard_datasets', '/dashboard/datasets', controller='ckanext.hdx_users.controllers.dashboard_controller:DashboardController', action='dashboard_datasets',
                  ckan_icon='sitemap')
        return map

    def get_actions(self):
        return {}
