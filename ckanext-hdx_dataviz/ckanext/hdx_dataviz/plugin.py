import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit

import ckanext.showcase.logic.schema as showcase_schema

import ckanext.hdx_dataviz.views.dataviz as dataviz
import ckanext.hdx_dataviz.helpers.helpers as h
from ckanext.hdx_dataviz.util.schema import showcase_update_schema_wrapper, showcase_show_schema_wrapper

request = toolkit.request


class HdxDatavizPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IBlueprint)
    plugins.implements(plugins.ITemplateHelpers)

    # IBlueprint
    def get_blueprint(self):
        return dataviz.hdx_dataviz_gallery

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
