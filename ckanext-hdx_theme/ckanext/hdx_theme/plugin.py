import ckanext.hdx_theme.licenses as hdx_licenses

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import ckan.model.package as package
import ckan.model.license as license
import version

import ckanext.hdx_theme.caching as caching



def run_on_startup():
    _generate_license_list()
    
    caching.cached_get_group_package_stuff()
    

def _generate_license_list():
    package.Package._license_register = license.LicenseRegister() 
    package.Package._license_register.licenses = [
                                                  license.License(hdx_licenses.LicenseCreativeCommonsIntergovernmentalOrgs()),
                                                  license.License(license.LicenseCreativeCommonsAttribution()),
                                                  license.License(license.LicenseCreativeCommonsAttributionShareAlike()),
                                                  license.License(hdx_licenses.LicenseCreativeCommonsNoDerives()),
                                                  license.License(hdx_licenses.LicenseOtherPublicDomainNoRestrictions()),
                                                  license.License(hdx_licenses.LicenseHdxMultiple()),
                                                  license.License(hdx_licenses.LicenseHdxOther())
                                                  ]

class HDXThemePlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IRoutes, inherit=True)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IGroupController, inherit=True)
    plugins.implements(plugins.IMiddleware, inherit=True)
    
    def update_config(self, config):
        toolkit.add_template_directory(config, 'templates')
        toolkit.add_public_directory(config, 'public')
        toolkit.add_resource('fanstatic', 'hdx_theme')
        

    def before_map(self, map):
        map.connect('home', '/', controller='ckanext.hdx_theme.splash_page:SplashPageController', action='index')
        map.connect('/count/dataset', controller='ckanext.hdx_theme.count:CountController', action='dataset')
        map.connect('/count/country', controller='ckanext.hdx_theme.count:CountController', action='country')
        map.connect('/count/source', controller='ckanext.hdx_theme.count:CountController', action='source')
        map.connect('/user/logged_in', controller='ckanext.hdx_theme.login:LoginController', action='logged_in')
        map.connect('/contribute', controller='ckanext.hdx_theme.login:LoginController', action='contribute')
        
        map.connect('/count/test', controller='ckanext.hdx_theme.count:CountController', action='test')
        
        return map
    
    def create(self, entity):
        caching.invalidate_group_caches()

    def edit(self, entity):
        caching.invalidate_group_caches()

    def get_helpers(self):
        from ckanext.hdx_theme import helpers as hdx_helpers
        return {
            'is_downloadable': hdx_helpers.is_downloadable,
            'get_facet_items_dict':hdx_helpers.get_facet_items_dict,
            'get_last_modifier_user': hdx_helpers.get_last_modifier_user,
            'get_filtered_params_list':hdx_helpers.get_filtered_params_list,
            'get_last_revision_package':hdx_helpers.get_last_revision_package,
            'get_last_modifier_user':hdx_helpers.get_last_modifier_user,
            'get_last_revision_group':hdx_helpers.get_last_revision_group,
            'get_group_followers':hdx_helpers.get_group_followers,
            'get_group_members':hdx_helpers.get_group_members,
            'markdown_extract_strip':hdx_helpers.markdown_extract_strip,
            'render_date_from_concat_str':hdx_helpers.render_date_from_concat_str,
            'hdx_version':hdx_helpers.hdx_version,
            'hdx_build_nav_icon_with_message':hdx_helpers.hdx_build_nav_icon_with_message,
            'hdx_num_of_new_related_items':hdx_helpers.hdx_num_of_new_related_items
        }
        
    def get_actions(self):
        from ckanext.hdx_theme import actions as hdx_actions
        return {
            'organization_list_for_user':hdx_actions.organization_list_for_user, 
            'cached_group_list': hdx_actions.cached_group_list
            
        }
    
    def make_middleware(self, app, config):
        run_on_startup()
        return app

        
        

