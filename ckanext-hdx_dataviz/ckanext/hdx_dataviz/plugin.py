import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit

import ckanext.showcase.logic.schema as showcase_schema

import ckanext.hdx_dataviz.views.dataviz as dataviz

import ckanext.hdx_dataviz.helpers.helpers as h
import ckanext.hdx_dataviz.actions.auth as auth
import ckanext.hdx_dataviz.actions.update as update
from ckanext.hdx_dataviz.util.schema import showcase_update_schema_wrapper, showcase_show_schema_wrapper

request = toolkit.request

@toolkit.blanket.config_declarations
class HdxDatavizPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    # if dataviz:
    plugins.implements(plugins.IBlueprint)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.IActions)

    # IBlueprint
    def get_blueprint(self):
        return [
            dataviz.hdx_dataviz_gallery
        ]

    # IConfigurer
    def update_config(self, config_):
        # toolkit.add_template_directory(config_, 'templates')
        # toolkit.add_public_directory(config_, 'public')
        # toolkit.add_resource('fanstatic', 'hdx_dataviz')

        # We can't implement IDatasetForm for the 'showcase' type so we need to do an ugly hack
        # in order to modify the validation schema for showcases
        showcase_schema.showcase_update_schema = showcase_update_schema_wrapper(showcase_schema.showcase_update_schema)
        showcase_schema.showcase_create_schema = showcase_update_schema_wrapper(showcase_schema.showcase_create_schema)
        showcase_schema.showcase_show_schema = showcase_show_schema_wrapper(showcase_schema.showcase_show_schema)

    # ITemplateHelpers
    def get_helpers(self):
        return {
            'has_dataviz_gallery_permission': h.has_dataviz_gallery_permission,
        }

    # IAuthFunctions
    def get_auth_functions(self):
        def wrap_get_auth_functions(plugin):
            original_get_auth_functions = plugin.get_auth_functions

            def _showcase_auth_functions():
                auth_functions = original_get_auth_functions()

                auth_functions.update({
                    'ckanext_showcase_create': auth.showcase_create,
                    'ckanext_showcase_update': auth.showcase_update,
                    'ckanext_showcase_delete': auth.showcase_delete,
                    'ckanext_showcase_package_association_create': auth.showcase_package_association_create,
                    'ckanext_showcase_package_association_delete': auth.showcase_package_association_delete,
                })
                return auth_functions

            plugin.get_auth_functions = _showcase_auth_functions

        for p in plugins.PluginImplementations(plugins.IAuthFunctions):
            if p.name == 'showcase':
                wrap_get_auth_functions(p)

        return {}

    # IActions
    def get_actions(self):

        return {
            'ckanext_showcase_update': update.chained_showcase_update
        }
