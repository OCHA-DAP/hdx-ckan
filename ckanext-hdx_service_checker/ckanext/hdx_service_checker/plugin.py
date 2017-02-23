import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit

import ckanext.hdx_service_checker.actions.get as actions
import ckanext.hdx_service_checker.actions.authorize as authorize


class HdxServiceCheckerPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.IRoutes, inherit=True)

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        # toolkit.add_public_directory(config_, 'public')
        # toolkit.add_resource('fanstatic', 'hdx_service_checker')

    def get_actions(self):
        return {
            'run_checks': actions.run_checks
        }

    def get_auth_functions(self):

        return {
            'run_checks': authorize.run_checks,
        }

    def before_map(self, map):
        map.connect('run_checks', '/run-checks', controller='ckanext.hdx_service_checker.controllers.checks_controller:ChecksController',
                  action='run_checks')
        return map