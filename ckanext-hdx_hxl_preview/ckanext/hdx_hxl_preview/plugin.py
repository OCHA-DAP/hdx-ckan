import logging
import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit

_ = plugins.toolkit._

log = logging.getLogger(__name__)

ignore_empty = plugins.toolkit.get_validator('ignore_empty')

class HdxHxlPreviewPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IResourceView, inherit=True)

    plugins.implements(plugins.IActions)

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'hdx_hxl_preview')

    def get_actions(self):
        return {
            # 'package_hxl_update': update.package_hxl_update
        }

    def can_view(self, data_dict):
        return True

    def info(self):

        schema = {
            "hxl_preview_config": [ignore_empty]
        }

        return {
            'name': 'hdx_hxl_preview',
            'title': 'HXL Preview',
            'filterable': False,
            'preview_enabled': True,
            'schema': schema,
            'requires_datastore': False,
            'iframed': True,
            'default_title': _('HXL Preview')
        }

    def setup_template_variables(self, context, data_dict):
        resource_view_dict = data_dict.get('resource_view')
        resource_dict = data_dict.get('resource')



    def view_template(self, context, data_dict):
        return 'hxl_preview.html'

    def form_template(self, context, data_dict):
        return 'hxl_preview_form.html'
