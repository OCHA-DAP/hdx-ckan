import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import ckanext.hdx_dataviz.views.dataviz as dataviz


class HdxDatavizPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IBlueprint)

    def get_blueprint(self):
        return dataviz.hdx_dataviz_gallery

    def update_config(self, config_):
        # toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'hdx_dataviz')
