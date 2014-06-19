import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit


def user_create(context, data_dict=None):
    #Disable registering new users
    return {'success': False, 'msg': 'Registering is disabled at the moment!'}


class DisableUserRegistration(plugins.SingletonPlugin):
#     plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IRoutes, inherit=True)

    def update_config(self, config):
        toolkit.add_template_directory(config, 'templates')

#     def get_auth_functions(self):
#         return {'user_create': user_create}

    def before_map(self, map):
#        Re-enabling user self-registration
#         map.connect('/user/request',
#                     controller='ckanext.register.request:RequestController',
#                     action='request')

        map.connect('/user/register',
                    controller='ckanext.register.request:RequestController',
                    action='register')
        map.connect('/user/logged_in', controller='ckanext.register.login:LoginController', action='logged_in')
        return map

#class LoginRedirect(plugins.SingletonPlugin):
#    plugins.implements(plugins.IConfigurer)
#    plugins.implements(plugins.IRoutes, inherit=True)
#    def update_config(self, config):
#        toolkit.add_template_directory(config, 'templates')
#
#    def before_map(self, map):
#        map.connect('/user/logged_in', controller='ckanext.register.login:LoginController', action='logged_in')
#        return map
