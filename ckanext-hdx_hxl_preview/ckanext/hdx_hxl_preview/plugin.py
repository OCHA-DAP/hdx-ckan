import logging


import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import ckan.authz as authz

import ckanext.hdx_hxl_preview.actions.update as update
import ckanext.hdx_hxl_preview.actions.get as get


_ = plugins.toolkit._
c = plugins.toolkit.c



log = logging.getLogger(__name__)

ignore_empty = plugins.toolkit.get_validator('ignore_empty')

@toolkit.blanket.config_declarations
class HdxHxlPreviewPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IResourceView, inherit=True)

    plugins.implements(plugins.IActions)

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_public_directory(config_, 'fanstatic')
        toolkit.add_resource('fanstatic', 'hdx_hxl_preview')

    def get_actions(self):
        return {
            'package_hxl_update': update.package_hxl_update,
            'hxl_preview_iframe_url_show': get.hxl_preview_iframe_url_show,
        }

    def can_view(self, data_dict):
        return True

    def info(self):

        schema = {
            "hxl_preview_config": [ignore_empty]
        }

        return {
            'name': 'hdx_hxl_preview',
            'title': 'Quick Charts',
            'filterable': False,
            'preview_enabled': True,
            'schema': schema,
            'requires_datastore': False,
            'iframed': False,
            'default_title': _('Quick Charts')
        }

    def setup_template_variables(self, context, data_dict):
        # resource_view_dict = data_dict.get('resource_view')
        resource_dict = data_dict.get('resource')

        # start_edit_mode = 'true' if self.__is_allowed_to_edit(resource_dict) and \
        #                   not self.__is_hxl_preview_config_saved(resource_view_dict) else 'false'

        has_modify_permission = authz.is_authorized_boolean('package_update', context, {'id': resource_dict.get('package_id')})
        return {
            'hxl_preview_full_url': get.hxl_preview_iframe_url_show({
                'has_modify_permission': has_modify_permission
            }, data_dict)
        }

    # def __is_hxl_preview_config_saved(self, resource_view_dict):
    #     try:
    #         hxl_preview_config = resource_view_dict.get('hxl_preview_config')
    #         if hxl_preview_config and json.loads(hxl_preview_config):
    #             return True
    #     except Exception, e:
    #         log.error('Couldn\'t check if hxl_preview_config exists: {}'.format(str(e)))
    #     return False
    #
    # def __is_allowed_to_edit(self, resource_dict):
    #     return ckan_helpers.check_access('package_update', {'id': resource_dict.get('package_id')})

    def view_template(self, context, data_dict):
        return 'hxl_preview.html'

    def form_template(self, context, data_dict):
        return 'hxl_preview_form.html'
