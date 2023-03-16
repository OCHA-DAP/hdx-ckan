import inspect
import json
import logging
import os

from six.moves.urllib.parse import urlparse, urlunparse

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import ckanext.hdx_theme.helpers.auth as auth
import ckanext.hdx_theme.helpers.custom_validator as custom_validator
import ckanext.hdx_theme.helpers.http_headers as http_headers
from ckanext.hdx_theme.cli.click_analytics_changes_reindex import analytics_changes_reindex
from ckanext.hdx_theme.cli.click_custom_less_compile import custom_less_compile
from ckanext.hdx_theme.middleware.cookie_middleware import CookieMiddleware
from ckanext.hdx_theme.middleware.redirection_middleware import RedirectionMiddleware
from ckanext.hdx_theme.util.http_exception_helper import FlaskEmailFilter
from ckanext.hdx_theme.views.archived_quick_links_custom_settings import hdx_archived_quick_links
from ckanext.hdx_theme.views.colored_page import hdx_colored_page
from ckanext.hdx_theme.views.count import hdx_count
from ckanext.hdx_theme.views.custom_pages import hdx_custom_pages
from ckanext.hdx_theme.views.custom_settings import hdx_carousel
from ckanext.hdx_theme.views.ebola import hdx_ebola
from ckanext.hdx_theme.views.faqs import hdx_faqs, hdx_main_faq
from ckanext.hdx_theme.views.image_server import hdx_global_file_server, hdx_local_image_server
from ckanext.hdx_theme.views.package_links_custom_settings import hdx_package_links
from ckanext.hdx_theme.views.quick_links_custom_settings import hdx_quick_links
from ckanext.hdx_theme.views.splash_page import hdx_splash
from ckanext.hdx_users.helpers.token_creation_notification_helper import send_email_on_token_creation

config = toolkit.config


class HDXThemePlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.IApiToken, inherit=True)
    plugins.implements(plugins.IMiddleware, inherit=True)
    plugins.implements(plugins.IValidators, inherit=True)
    plugins.implements(plugins.IBlueprint)
    plugins.implements(plugins.IClick)

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

    # IConfigurer
    def update_config(self, config):
        toolkit.add_template_directory(config, 'templates')
        toolkit.add_template_directory(config, 'templates_legacy')
        toolkit.add_public_directory(config, 'public')
        # self._add_resource('fanstatic', 'hdx_theme')
        toolkit.add_public_directory(config, 'fanstatic')
        toolkit.add_resource('fanstatic', 'hdx_theme')
        # Add configs needed for checks
        self.__add_dataproxy_url_for_checks(config)
        self.__add_gis_layer_config_for_checks(config)
        self.__add_spatial_config_for_checks(config)
        self.__add_hxl_proxy_url_for_checks(config)
        self.__add_wp_faq_url_for_checks(config)

    def __add_dataproxy_url_for_checks(self, config):
        dataproxy_url = config.get('ckan.recline.dataproxy_url', '')
        dataproxy_url = self._create_full_URL(dataproxy_url)
        config['hdx_checks.dataproxy_url'] = dataproxy_url

    def __add_gis_layer_config_for_checks(self, config):
        gis_layer_api = config.get('hdx.gis.layer_import_url', '')
        api_index = gis_layer_api.find('/api')
        gis_layer_base_api = gis_layer_api[0:api_index]
        gis_layer_base_api = self._create_full_URL(gis_layer_base_api)
        config['hdx_checks.gis_layer_base_url'] = gis_layer_base_api

    def __add_spatial_config_for_checks(self, config):
        # search_str = '/services'
        spatial_url = config.get('hdx.gis.resource_pbf_url', '')
        url_parts = urlparse(spatial_url)
        spatial_check_url = urlunparse((url_parts.scheme, url_parts.netloc, '/gis/test', '', '', ''))
        # url_index = spatial_url.find(search_str)
        # spatial_check_url = spatial_url[0:url_index + len(search_str)]
        spatial_check_url = self._create_full_URL(spatial_check_url)
        config['hdx_checks.spatial_checks_url'] = spatial_check_url

    def __add_hxl_proxy_url_for_checks(self, config):
        hxl_proxy_url = self._create_full_URL('/hxlproxy/data.json?url=sample.test')
        config['hdx_checks.hxl_proxy_url'] = hxl_proxy_url

    def __add_wp_faq_url_for_checks(self, config):
        wp_url = '{0}/custom-ufaq-category/{1}'\
            .format(config.get('hdx.wordpress.url'), config.get('hdx.wordpress.category.faq'))
        config['hdx_checks.wp_faq_url'] = wp_url
        basic_auth = config.get('hdx.wordpress.auth.basic')
        if not basic_auth:
            basic_auth = "None"
        config['hdx_checks.wp_basic_auth'] = basic_auth

    def _create_full_URL(self, url):
        '''
        Different URLs specified in prod.ini might be relative URLs or be
        protocol independent.
        This function tries to guess the full URL.

        :param url: the url to be modified if needed
        :type url: str
        '''
        urlobj = urlparse(url)
        if not urlobj.netloc:
            base_url = config.get('ckan.site_url')
            base_urlobj = urlparse(base_url)
            urlobj = urlobj._replace(scheme=base_urlobj.scheme)
            urlobj = urlobj._replace(netloc=base_urlobj.netloc)

        if not urlobj.scheme:
            urlobj = urlobj._replace(scheme='https')

        return urlobj.geturl()

    # IConfigurer
    def update_config_schema(self, schema):
        _clean_alert_bar_title_when_no_url = \
            toolkit.get_converter('hdx_clean_field_based_on_other_field_wrapper')('hdx.alert_bar_url')
        schema.update({
            'hdx.alert_bar_url': [
                toolkit.get_validator('ignore_empty'),
                toolkit.get_validator('unicode_only'),
                toolkit.get_validator('hdx_is_url'),
            ],
            'hdx.alert_bar_title': [
                _clean_alert_bar_title_when_no_url,
                toolkit.get_validator('ignore_empty'),
                toolkit.get_validator('unicode_only'),
                toolkit.get_validator('hdx_check_string_length_wrapper')(40),
            ],
        })
        return schema

    # def before_map(self, map):
        # map.connect(
        #     'hdx_home', '/', controller='ckanext.hdx_theme.splash_page:SplashPageController', action='index')
        # map.connect(
        #     '/count/dataset', controller='ckanext.hdx_theme.helpers.count:CountController', action='dataset')
        # map.connect(
        #     '/count/country', controller='ckanext.hdx_theme.helpers.count:CountController', action='country')
        # map.connect(
        #     '/count/source', controller='ckanext.hdx_theme.helpers.count:CountController', action='source')
        # map.connect('/user/logged_in', controller='ckanext.hdx_theme.login:LoginController', action='logged_in')
        # map.connect('/contribute', controller='ckanext.hdx_theme.login:LoginController', action='contribute')

        # map.connect(
        #     '/about/{page}', controller='ckanext.hdx_theme.splash_page:SplashPageController', action='about')

        # map.connect(
        #     '/about/license/legacy_hrinfo', controller='ckanext.hdx_theme.splash_page:SplashPageController',
        #     action='about_hrinfo')

        # map.connect(
        #     '/widget/topline', controller='ckanext.hdx_theme.controllers.widget_topline:WidgetToplineController',
        #     action='show')
        # map.connect(
        #     '/widget/3W', controller='ckanext.hdx_theme.controllers.widget_3W:Widget3WController', action='show')
        # map.connect(
        #     '/widget/WFP', controller='ckanext.hdx_theme.controllers.widget_WFP:WidgetWFPController', action='show')

        # map.connect('pages_show', '/ckan-admin/pages/show',
        #             controller='ckanext.hdx_theme.controllers.custom_settings:CustomSettingsController',
        #             action='show_pages')

        # return map

    def get_helpers(self):
        from ckanext.hdx_theme.helpers import helpers as hdx_helpers
        from ckanext.hdx_theme.helpers.constants import const
        return {
            'is_downloadable': hdx_helpers.is_downloadable,
            'is_not_zipped': hdx_helpers.is_not_zipped,
            'is_not_hxl_format': hdx_helpers.is_not_hxl_format,
            'get_facet_items_dict': hdx_helpers.get_facet_items_dict,
            'get_last_modifier_user': hdx_helpers.get_last_modifier_user,
            'get_filtered_params_list': hdx_helpers.get_filtered_params_list,
            # 'get_last_revision_package': hdx_helpers.get_last_revision_package,
            # 'get_last_revision_group': hdx_helpers.get_last_revision_group,
            'get_group_followers': hdx_helpers.get_group_followers,
            'get_group_members': hdx_helpers.get_group_members,
            'markdown_extract_strip': hdx_helpers.markdown_extract_strip,
            'render_markdown_strip': hdx_helpers.render_markdown_strip,
            'render_date_from_concat_str': hdx_helpers.render_date_from_concat_str,
            'hdx_version': hdx_helpers.hdx_version,
            'hdx_build_nav_icon_with_message': hdx_helpers.hdx_build_nav_icon_with_message,
            'hdx_build_nav_no_icon': hdx_helpers.hdx_build_nav_no_icon,
            'hdx_num_of_new_related_items': hdx_helpers.hdx_num_of_new_related_items,
            'hdx_user_count': hdx_helpers.hdx_user_count,
            'hdx_get_extras_element': hdx_helpers.hdx_get_extras_element,
            'hdx_get_user_info': hdx_helpers.hdx_get_user_info,
            'hdx_get_org_member_info': hdx_helpers.hdx_get_org_member_info,
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
            'hdx_popular': hdx_helpers.hdx_popular,
            'get_dataset_date_format': hdx_helpers.get_dataset_date_format,
            'hdx_methodology_list': hdx_helpers.hdx_methodology_list,
            'hdx_license_list': hdx_helpers.hdx_license_list,
            'hdx_location_list': hdx_helpers.hdx_location_list,
            'hdx_organisation_list': hdx_helpers.hdx_organisation_list,
            'hdx_tag_list': hdx_helpers.hdx_tag_list,
            'hdx_frequency_list': hdx_helpers.hdx_frequency_list,
            # 'hdx_get_layer_info': hdx_helpers.hdx_get_layer_info,
            'hdx_get_carousel_list': hdx_helpers.hdx_get_carousel_list,
            'hdx_get_quick_links_list': hdx_helpers.hdx_get_quick_links_list,
            'hdx_get_frequency_by_value': hdx_helpers.hdx_get_frequency_by_value,
            'hdx_is_current_user_a_maintainer': hdx_helpers.hdx_is_current_user_a_maintainer,
            'hdx_dataset_follower_count': hdx_helpers.hdx_dataset_follower_count,
            'hdx_organization_list_for_user': hdx_helpers.hdx_organization_list_for_user,
            'hdx_is_sysadmin': hdx_helpers.hdx_is_sysadmin,
            'hdx_dataset_preview_values_list': hdx_helpers.hdx_dataset_preview_values_list,
            'hdx_dataset_is_hxl': hdx_helpers.hdx_dataset_is_hxl,
            'hdx_dataset_has_sadd': hdx_helpers.hdx_dataset_has_sadd,
            'hdx_switch_url_path': hdx_helpers.switch_url_path,
            'hdx_munge_title': hdx_helpers.hdx_munge_title,
            'hdx_url_for': hdx_helpers.hdx_url_for,
            'hdx_check_http_response': hdx_helpers.hdx_check_http_response,
            'hdx_get_request_param': hdx_helpers.hdx_get_request_param,
            'hdx_pending_request_data': hdx_helpers.hdx_pending_request_data,
            'HDX_CONST': const
        }

    def get_actions(self):
        from ckanext.hdx_theme.helpers import actions as hdx_actions
        return {
            'hdx_organization_list_for_user': hdx_actions.hdx_organization_list_for_user,
            'cached_group_list': hdx_actions.cached_group_list,
            'cached_organization_list': hdx_actions.cached_organization_list,
            'invalidate_cache_for_groups': hdx_actions.invalidate_cache_for_groups,
            'invalidate_cache_for_organizations': hdx_actions.invalidate_cache_for_organizations,
            'invalidate_cached_resource_id_apihighways': hdx_actions.invalidate_cached_resource_id_apihighways,
            'invalidate_region': hdx_actions.invalidate_region,
            'hdx_basic_user_info': hdx_actions.hdx_basic_user_info,
            'member_list': hdx_actions.member_list,
            # 'hdx_get_sys_admins': hdx_actions.hdx_get_sys_admins,
            # 'hdx_send_new_org_request': hdx_actions.hdx_send_new_org_request,
            'hdx_send_editor_request_for_org': hdx_actions.hdx_send_editor_request_for_org,
            # 'hdx_send_request_membership': hdx_actions.hdx_send_request_membership,
            # 'hdx_user_show': hdx_actions.hdx_user_show,
            'hdx_get_indicator_values': hdx_actions.hdx_get_indicator_values,
            # 'hdx_get_shape_geojson': hdx_actions.hdx_get_shape_geojson,
            # 'hdx_get_shape_info': hdx_actions.hdx_get_shape_info,
            # 'hdx_get_indicator_available_periods': hdx_actions.hdx_get_indicator_available_periods,
            'hdx_carousel_settings_show': hdx_actions.hdx_carousel_settings_show,
            'hdx_carousel_settings_update': hdx_actions.hdx_carousel_settings_update,
            # 'hdx_get_json_from_resource':hdx_actions.hdx_get_json_from_resource
            # 'hdx_get_activity_list': hdx_actions.hdx_get_activity_list
            'hdx_general_statistics': hdx_actions.hdx_general_statistics,
            'hdx_user_statistics': hdx_actions.hdx_user_statistics,
            'hdx_organization_statistics': hdx_actions.hdx_organization_statistics,
            'hdx_push_general_stats': hdx_actions.hdx_push_general_stats,
            'hdx_quick_links_settings_show': hdx_actions.hdx_quick_links_settings_show,
            'hdx_quick_links_settings_update': hdx_actions.hdx_quick_links_settings_update,
            'hdx_package_links_settings_show': hdx_actions.package_links_settings_show,
            'hdx_package_links_settings_update': hdx_actions.package_links_settings_update,
            'hdx_package_links_by_id_list': hdx_actions.package_links_by_id_list,
            'activity_detail_list': hdx_actions.hdx_activity_detail_list,
        }

    def get_auth_functions(self):
        return {
            'hdx_basic_user_info': auth.hdx_basic_user_info,
            'group_member_create': auth.group_member_create,
            # 'hdx_send_new_org_request': auth.hdx_send_new_org_request,
            'hdx_send_editor_request_for_org': auth.hdx_send_editor_request_for_org,
            'invalidate_cache_for_groups': auth.invalidate_cache_for_groups,
            'invalidate_cache_for_organizations': auth.invalidate_cache_for_organizations,
            'invalidate_cached_resource_id_apihighways': auth.invalidate_cached_resource_id_apihighways,
            'invalidate_region': auth.invalidate_region,
            'hdx_user_statistics': auth.hdx_user_statistics,
            'hdx_push_general_stats': auth.hdx_push_general_stats,
            'hdx_carousel_update': auth.hdx_carousel_update,
            'hdx_request_data_admin_list': auth.hdx_request_data_admin_list,
            'hdx_quick_links_update': auth.hdx_quick_links_update,
            'user_generate_apikey': auth.hdx_user_generate_apikey,
        }

    # IMiddleware
    def make_middleware(self, app, config):
        cookie_app = CookieMiddleware(app, config)
        redirection_app = RedirectionMiddleware(cookie_app, config)
        if app.app_name == 'flask_app':
            from logging.handlers import SMTPHandler
            for handler in app.logger.handlers:
                if isinstance(handler, SMTPHandler):
                    handler.setLevel(logging.ERROR)
            app.logger.addFilter(FlaskEmailFilter())
            app.after_request(http_headers.set_http_headers)
        return redirection_app

    # IValidators
    def get_validators(self):
        return {
            'doesnt_exceed_max_validity_period': custom_validator.doesnt_exceed_max_validity_period,
            'hdx_is_url': custom_validator.hdx_is_url,
            'hdx_check_string_length_wrapper': custom_validator.hdx_check_string_length_wrapper,
            'hdx_clean_field_based_on_other_field_wrapper':
                custom_validator.hdx_clean_field_based_on_other_field_wrapper,
        }

    # IApiToken
    def create_api_token_schema(self, schema):
        # add to the schema from expire_api_token plugin
        schema['expires_in'].append(toolkit.get_validator('doesnt_exceed_max_validity_period'))
        return schema

    # IApiToken
    def postprocess_api_token(self, data, jti, data_dict):
        send_email_on_token_creation(data_dict.get('user'), data_dict.get('name'), data.get('exp'))
        return data

    # IBlueprint
    def get_blueprint(self):
        return [hdx_colored_page, hdx_faqs, hdx_main_faq, hdx_ebola, hdx_global_file_server,
                hdx_local_image_server, hdx_carousel, hdx_custom_pages,
                hdx_quick_links, hdx_package_links, hdx_archived_quick_links, hdx_splash, hdx_count]

    # IClick
    def get_commands(self):
        return [custom_less_compile, analytics_changes_reindex]
