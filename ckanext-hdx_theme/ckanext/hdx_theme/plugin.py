import inspect
import json
import os
import urlparse

import ckanext.hdx_package.helpers.caching as caching
import ckanext.hdx_theme.helpers.auth as auth
import pylons.config as config

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit


# def run_on_startup():
#     cache_on_startup = config.get('hdx.cache.onstartup', 'true')
#     if 'true' == cache_on_startup:
#         _generate_license_list()
#         caching.cached_get_group_package_stuff()


# def _generate_license_list():
#     package.Package._license_register = license.LicenseRegister()
#     package.Package._license_register.licenses = [
#                                                   license.License(hdx_licenses.LicenseCreativeCommonsIntergovernmentalOrgs()),
#                                                   license.License(license.LicenseCreativeCommonsAttribution()),
#                                                   license.License(license.LicenseCreativeCommonsAttributionShareAlike()),
#                                                   license.License(hdx_licenses.LicenseOtherPublicDomainNoRestrictions()),
#                                                   license.License(hdx_licenses.LicenseHdxMultiple()),
#                                                   license.License(hdx_licenses.LicenseHdxOther())
#                                                   ]

class HDXThemePlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IRoutes, inherit=True)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.IGroupController, inherit=True)
    plugins.implements(plugins.IMiddleware, inherit=True)

    def _add_resource(cls, path, name):
        '''OVERRIDE toolkit.add_resource in order to allow adding a resource library
         without the dependency to the base/main resource library

        See: toolkit.py:_add_resource(cls,path,name) for more details

        '''
        # we want the filename that of the function caller but they will
        # have used one of the available helper functions
        frame, filename, line_number, function_name, lines, index = \
            inspect.getouterframes(inspect.currentframe())[1]

        this_dir = os.path.dirname(filename)
        absolute_path = os.path.join(this_dir, path)
        import ckan.lib.fanstatic_resources
        ckan.lib.fanstatic_resources.create_library(name, absolute_path, False)

    def update_config(self, config):
        toolkit.add_template_directory(config, 'templates')
        toolkit.add_template_directory(config, 'templates_legacy')
        toolkit.add_public_directory(config, 'public')
        #self._add_resource('fanstatic', 'hdx_theme')
        toolkit.add_resource('fanstatic', 'hdx_theme')
        # Add configs needed for checks
        self.__add_dataproxy_url_for_checks(config)
        self.__add_gis_layer_config_for_checks(config)
        self.__add_spatial_config_for_checks(config)

    def __add_dataproxy_url_for_checks(self, config):
        dataproxy_url = config.get('hdx.datapreview.url', '')
        dataproxy_url = self._create_full_URL(dataproxy_url)
        config['hdx_checks.dataproxy_url'] = dataproxy_url

    def __add_gis_layer_config_for_checks(self, config):
        gis_layer_api = config.get('hdx.gis.layer_import_url', '')
        api_index = gis_layer_api.find('/api')
        gis_layer_base_api = gis_layer_api[0:api_index]
        gis_layer_base_api = self._create_full_URL(gis_layer_base_api)
        config['hdx_checks.gis_layer_base_url'] = gis_layer_base_api

    def __add_spatial_config_for_checks(self, config):
        search_str = '/services'
        spatial_url = config.get('hdx.gis.resource_pbf_url', '')
        url_index = spatial_url.find(search_str)
        spatial_check_url = spatial_url[0:url_index+len(search_str)]
        spatial_check_url = self._create_full_URL(spatial_check_url)
        config['hdx_checks.spatial_checks_url'] = spatial_check_url

    def _create_full_URL(self, url):
        '''
        Different URLs specified in prod.ini might be relative URLs or be
        protocol independent.
        This function tries to guess the full URL.

        :param url: the url to be modified if needed
        :type url: str
        '''
        urlobj = urlparse.urlparse(url)
        if not urlobj.netloc:
            base_url = config.get('ckan.site_url')
            base_urlobj = urlparse.urlparse(base_url)
            urlobj = urlobj._replace(scheme=base_urlobj.scheme)
            urlobj = urlobj._replace(netloc=base_urlobj.netloc)

        if not urlobj.scheme:
            urlobj = urlobj._replace(scheme='https')

        return urlobj.geturl()

    def before_map(self, map):
        map.connect(
            'home', '/', controller='ckanext.hdx_theme.splash_page:SplashPageController', action='index')
        map.connect(
            '/count/dataset', controller='ckanext.hdx_theme.helpers.count:CountController', action='dataset')
        map.connect(
            '/count/country', controller='ckanext.hdx_theme.helpers.count:CountController', action='country')
        map.connect(
            '/count/source', controller='ckanext.hdx_theme.helpers.count:CountController', action='source')
        #map.connect('/user/logged_in', controller='ckanext.hdx_theme.login:LoginController', action='logged_in')
        #map.connect('/contribute', controller='ckanext.hdx_theme.login:LoginController', action='contribute')

        map.connect(
            '/count/test', controller='ckanext.hdx_theme.helpers.count:CountController', action='test')
        map.connect(
            '/about/{page}', controller='ckanext.hdx_theme.splash_page:SplashPageController', action='about')

        map.connect(
            '/about/license/legacy_hrinfo', controller='ckanext.hdx_theme.splash_page:SplashPageController', action='about_hrinfo')

        map.connect(
            '/widget/topline', controller='ckanext.hdx_theme.controllers.widget_topline:WidgetToplineController', action='show')
        map.connect(
            '/widget/3W', controller='ckanext.hdx_theme.controllers.widget_3W:Widget3WController', action='show')
        map.connect(
            '/widget/WFP', controller='ckanext.hdx_theme.controllers.widget_WFP:WidgetWFPController', action='show')

        map.connect(
            '/faq', controller='ckanext.hdx_theme.controllers.faq:FaqController', action='show')
        map.connect(
            '/faq/contact_us', controller='ckanext.hdx_theme.controllers.faq:FaqController', action='contact_us')

        map.connect('/explore', controller='ckanext.hdx_theme.controllers.explorer:ExplorerController', action='show')

        #map.connect('resource_edit', '/dataset/{id}/resource_edit/{resource_id}', controller='ckanext.hdx_theme.package_controller:HDXPackageController', action='resource_edit', ckan_icon='edit')

        map.connect('carousel_settings', '/ckan-admin/carousel/show',
                    controller='ckanext.hdx_theme.controllers.custom_settings:CustomSettingsController', action='show')

        map.connect('global_file_download', '/global/{filename}',
                    controller='ckanext.hdx_theme.controllers.global_file_server:GlobalFileController',
                    action='global_file_download')

        map.connect('update_carousel_settings', '/ckan-admin/carousel/update',
                    controller='ckanext.hdx_theme.controllers.custom_settings:CustomSettingsController', action='update')

        map.connect('delete_carousel_settings', '/ckan-admin/carousel/delete/{id}',
                    controller='ckanext.hdx_theme.controllers.custom_settings:CustomSettingsController',
                    action='delete')

        return map

    def create(self, entity):
        caching.invalidate_group_caches()

    def edit(self, entity):
        caching.invalidate_group_caches()

    def get_helpers(self):
        from ckanext.hdx_theme.helpers import helpers as hdx_helpers
        return {
            'is_downloadable': hdx_helpers.is_downloadable,
            'is_not_zipped': hdx_helpers.is_not_zipped,
            'get_facet_items_dict': hdx_helpers.get_facet_items_dict,
            'get_last_modifier_user': hdx_helpers.get_last_modifier_user,
            'get_filtered_params_list': hdx_helpers.get_filtered_params_list,
            'get_last_revision_package': hdx_helpers.get_last_revision_package,
            'get_last_revision_group': hdx_helpers.get_last_revision_group,
            'get_group_followers': hdx_helpers.get_group_followers,
            'get_group_members': hdx_helpers.get_group_members,
            'markdown_extract_strip': hdx_helpers.markdown_extract_strip,
            'render_markdown_strip': hdx_helpers.render_markdown_strip,
            'render_date_from_concat_str': hdx_helpers.render_date_from_concat_str,
            'hdx_version': hdx_helpers.hdx_version,
            'hdx_build_nav_icon_with_message': hdx_helpers.hdx_build_nav_icon_with_message,
            'hdx_build_nav_no_icon': hdx_helpers.hdx_build_nav_no_icon,
            'hdx_num_of_new_related_items': hdx_helpers.hdx_num_of_new_related_items,
            'hdx_get_extras_element': hdx_helpers.hdx_get_extras_element,
            'hdx_get_user_info': hdx_helpers.hdx_get_user_info,
            'hdx_linked_user': hdx_helpers.hdx_linked_user,
            'hdx_show_singular_plural': hdx_helpers.hdx_show_singular_plural,
            'hdx_member_roles_list': hdx_helpers.hdx_member_roles_list,
            'hdx_organizations_available_with_roles': hdx_helpers.hdx_organizations_available_with_roles,
            'hdx_group_followee_list': hdx_helpers.hdx_group_followee_list,
            'hdx_follow_link': hdx_helpers.hdx_follow_link,
            'hdx_remove_schema_and_domain_from_url': hdx_helpers.hdx_remove_schema_and_domain_from_url,
            'hdx_get_ckan_config': hdx_helpers.hdx_get_ckan_config,
            'get_group_name_from_list': hdx_helpers.get_group_name_from_list,
            'one_active_item': hdx_helpers.one_active_item,
            'hdx_follow_button': hdx_helpers.hdx_follow_button,
            'get_last_revision_timestamp_group': hdx_helpers.get_last_revision_timestamp_group,
            'feature_count': hdx_helpers.feature_count,
            'follow_status': hdx_helpers.follow_status,
            'hdx_add_url_param': hdx_helpers.hdx_add_url_param,
            'methodology_bk_compat': hdx_helpers.methodology_bk_compat,
            'count_public_datasets_for_group': hdx_helpers.count_public_datasets_for_group,
            'hdx_resource_preview': hdx_helpers.hdx_resource_preview,
            'load_json': hdx_helpers.load_json,
            'escaped_dump_json': hdx_helpers.escaped_dump_json,
            'json_dumps': json.dumps,
            'hdx_less_default': hdx_helpers.hdx_less_default,
            'hdx_popular': hdx_helpers.hdx_popular,
            'hdx_escape': hdx_helpers.hdx_escape,
            'get_dataset_date_format': hdx_helpers.get_dataset_date_format,
            'hdx_methodology_list': hdx_helpers.hdx_methodology_list,
            'hdx_license_list': hdx_helpers.hdx_license_list,
            'hdx_location_list': hdx_helpers.hdx_location_list,
            'hdx_organisation_list': hdx_helpers.hdx_organisation_list,
            'hdx_tag_list': hdx_helpers.hdx_tag_list,
            'hdx_frequency_list': hdx_helpers.hdx_frequency_list,
            'hdx_get_layer_info': hdx_helpers.hdx_get_layer_info,
            'hdx_get_carousel_list': hdx_helpers.hdx_get_carousel_list
        }

    def get_actions(self):
        from ckanext.hdx_theme.helpers import actions as hdx_actions
        return {
            'organization_list_for_user': hdx_actions.organization_list_for_user,
            'cached_group_list': hdx_actions.cached_group_list,
            'hdx_basic_user_info': hdx_actions.hdx_basic_user_info,
            'member_list': hdx_actions.member_list,
            # 'hdx_get_sys_admins': hdx_actions.hdx_get_sys_admins,
            'hdx_send_new_org_request': hdx_actions.hdx_send_new_org_request,
            'hdx_send_editor_request_for_org': hdx_actions.hdx_send_editor_request_for_org,
            'hdx_send_request_membership': hdx_actions.hdx_send_request_membership,
            'hdx_user_show': hdx_actions.hdx_user_show,
            'hdx_get_indicator_values': hdx_actions.hdx_get_indicator_values,
            # 'hdx_get_shape_geojson': hdx_actions.hdx_get_shape_geojson,
            # 'hdx_get_shape_info': hdx_actions.hdx_get_shape_info,
            'hdx_get_indicator_available_periods': hdx_actions.hdx_get_indicator_available_periods,
            'hdx_carousel_settings_show': hdx_actions.hdx_carousel_settings_show,
            'hdx_carousel_settings_update': hdx_actions.hdx_carousel_settings_update
            # 'hdx_get_json_from_resource':hdx_actions.hdx_get_json_from_resource
            #'hdx_get_activity_list': hdx_actions.hdx_get_activity_list
        }

    def get_auth_functions(self):
        return {
            'hdx_basic_user_info': auth.hdx_basic_user_info,
            'group_member_create': auth.group_member_create,
            'hdx_send_new_org_request': auth.hdx_send_new_org_request,
            'hdx_send_editor_request_for_org': auth.hdx_send_editor_request_for_org,
            'hdx_send_request_membership': auth.hdx_send_request_membership
        }

        # def make_middleware(self, app, config):
        #     run_on_startup()
        #     return app
