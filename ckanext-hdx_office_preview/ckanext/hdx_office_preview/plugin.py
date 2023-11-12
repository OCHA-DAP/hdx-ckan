import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import logging

log = logging.getLogger(__name__)
class Hdx_Office_PreviewPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IResourceView, inherit=True)

    # IResourceView
    def info(self):
        # log.info('Setting up Office Preview!')
        return {
            'name': 'hdx_office_preview',
            'title': 'Office Preview',
            'filterable': True,
            'icon': 'file-text-o',
            'requires_datastore': False,
            'iframed': True,
            'preview_enabled': True,
            'preview_is_framed': True,
            'default_title': 'Office Preview'
        }

    def can_view(self, data_dict):
        resource = data_dict['resource']
        format_lower = resource['format'].lower()
        # log.info('Checking if resource format is supported: %s', format_lower)
        return format_lower in ['xls', 'xlsx', 'doc', 'docx', 'ppt', 'pptx', 'odt', 'ods', 'odp']

    def setup_template_variables(self, context, data_dict):
        resource = data_dict['resource']
        format_lower = resource['format'].lower()
        url = resource['url']
        return {'res': resource, 'format_lower': format_lower, 'url': url}

    def view_template(self, context, data_dict):
        return 'hdx_office_preview_view.html'
    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'hdx_office_preview')
