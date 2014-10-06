import ckanext.hdx_package.helpers.licenses as hdx_licenses

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import ckan.model.package as package
import ckan.model.license as license
import pylons.config as config
import version

import ckanext.hdx_package.helpers.caching as caching
import ckanext.hdx_theme.helpers.auth as auth


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
    
    def update_config(self, config):
        toolkit.add_template_directory(config, 'templates')
        toolkit.add_template_directory(config, 'templates_legacy')
        toolkit.add_public_directory(config, 'public')
        toolkit.add_resource('fanstatic', 'hdx_theme')
        

    def before_map(self, map):
        map.connect('home', '/', controller='ckanext.hdx_theme.splash_page:SplashPageController', action='index')
        map.connect('/count/dataset', controller='ckanext.hdx_theme.helpers.count:CountController', action='dataset')
        map.connect('/count/country', controller='ckanext.hdx_theme.helpers.count:CountController', action='country')
        map.connect('/count/source', controller='ckanext.hdx_theme.helpers.count:CountController', action='source')
        #map.connect('/user/logged_in', controller='ckanext.hdx_theme.login:LoginController', action='logged_in')
        #map.connect('/contribute', controller='ckanext.hdx_theme.login:LoginController', action='contribute')
        
        map.connect('/count/test', controller='ckanext.hdx_theme.helpers.count:CountController', action='test')
        map.connect('/about/{page}', controller='ckanext.hdx_theme.splash_page:SplashPageController', action='about')

        #map.connect('resource_edit', '/dataset/{id}/resource_edit/{resource_id}', controller='ckanext.hdx_theme.package_controller:HDXPackageController', action='resource_edit', ckan_icon='edit')

        return map
    
    def create(self, entity):
        caching.invalidate_group_caches()

    def edit(self, entity):
        caching.invalidate_group_caches()

    def get_helpers(self):
        from ckanext.hdx_theme.helpers import helpers as hdx_helpers
        return {
            'is_downloadable': hdx_helpers.is_downloadable,
            'get_facet_items_dict': hdx_helpers.get_facet_items_dict,
            'get_last_modifier_user': hdx_helpers.get_last_modifier_user,
            'get_filtered_params_list': hdx_helpers.get_filtered_params_list,
            'get_last_revision_package': hdx_helpers.get_last_revision_package,
            'get_last_modifier_user': hdx_helpers.get_last_modifier_user,
            'get_last_revision_group': hdx_helpers.get_last_revision_group,
            'get_group_followers': hdx_helpers.get_group_followers,
            'get_group_members': hdx_helpers.get_group_members,
            'markdown_extract_strip': hdx_helpers.markdown_extract_strip,
            'render_date_from_concat_str': hdx_helpers.render_date_from_concat_str,
            'hdx_version': hdx_helpers.hdx_version,
            'hdx_build_nav_icon_with_message': hdx_helpers.hdx_build_nav_icon_with_message,
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
            'feature_count': hdx_helpers.feature_count
        }
        
    def get_actions(self):
        from ckanext.hdx_theme.helpers import actions as hdx_actions
        return {
            'organization_list_for_user':hdx_actions.organization_list_for_user, 
            'cached_group_list': hdx_actions.cached_group_list,
            'hdx_basic_user_info': hdx_actions.hdx_basic_user_info,
            'member_list': hdx_actions.member_list,
            'hdx_get_sys_admins': hdx_actions.hdx_get_sys_admins,
            'hdx_send_new_org_request': hdx_actions.hdx_send_new_org_request,
            'hdx_send_editor_request_for_org': hdx_actions.hdx_send_editor_request_for_org,
            'hdx_send_request_membership': hdx_actions.hdx_send_request_membership,
            'hdx_user_show' : hdx_actions.hdx_user_show,
            'hdx_get_indicator_values': hdx_actions.hdx_get_indicator_values
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

        
        

