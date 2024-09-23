import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit

import ckanext.hdx_service_checker.actions.get as actions
import ckanext.hdx_service_checker.actions.authorize as authorize
import ckanext.hdx_service_checker.views.run_checks as run_checks

@toolkit.blanket.config_declarations
class HdxServiceCheckerPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.IBlueprint)

    # IConfigurer
    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        # toolkit.add_public_directory(config_, 'public')
        # toolkit.add_resource('fanstatic', 'hdx_service_checker')

    #IActions
    def get_actions(self):
        return {
            'run_checks': actions.run_checks
        }

    # IAuthFunctions
    def get_auth_functions(self):

        return {
            'run_checks': authorize.run_checks,
        }

    # IBlueprint
    def get_blueprint(self):
        return run_checks.hdx_run_checks
