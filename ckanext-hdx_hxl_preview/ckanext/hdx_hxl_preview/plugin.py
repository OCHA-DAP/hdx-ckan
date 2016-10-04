import logging
import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit

_ = plugins.toolkit._

log = logging.getLogger(__name__)

class HdxHxlPreviewPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IResourceView, inherit=True)

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'hdx_hxl_preview')

    def can_view(self, data_dict):
        return True

    def info(self):
        return {
            'name': 'hdx_hxl_preview',
            'title': 'HXL Preview',
            'filterable': False,
            'preview_enabled': True,
            'requires_datastore': False,
            'iframed': True,
            'default_title': _('HXL Preview')
        }

    def setup_template_variables(self, context, data_dict):
        resource_view_dict = data_dict.get('resource_view')
        resource_dict = data_dict.get('resource_view')



    def view_template(self, context, data_dict):
        return 'hxl_preview.html'

    def form_template(self, context, data_dict):
        return 'hxl_preview_form.html'
