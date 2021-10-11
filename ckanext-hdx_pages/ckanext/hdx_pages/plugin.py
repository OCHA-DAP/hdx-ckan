import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit

import ckanext.hdx_pages.actions.create as create
import ckanext.hdx_pages.actions.delete as delete
import ckanext.hdx_pages.actions.update as update
import ckanext.hdx_pages.actions.get as get
import ckanext.hdx_pages.actions.auth as auth

import ckanext.hdx_pages.helpers.helper as helper
import ckanext.hdx_pages.model as pages_model

import ckanext.hdx_pages.views.light_page as light_page


# class HdxPagesPlugin(plugins.SingletonPlugin):
#
#
#

class HdxCustomPagesPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IBlueprint)
    plugins.implements(plugins.IActions, inherit=True)
    plugins.implements(plugins.IAuthFunctions, inherit=True)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IConfigurable)
    plugins.implements(plugins.IRoutes, inherit=True)

    # IBlueprint
    def get_blueprint(self):
        return [
            light_page.hdx_light_event,
            light_page.hdx_light_dashboard,
            # HDX-7859 TO BE uncommented when search extension is migrated to py3
            light_page.hdx_event,
            light_page.hdx_dashboard,
            light_page.hdx_custom_page
        ]

    # IActions
    def get_actions(self):
        return {
            'page_create': create.page_create,
            'page_delete': delete.page_delete,
            'page_update': update.page_update,
            'page_show': get.page_show,
            'page_group_list': get.page_group_list,
            'group_page_list': get.group_page_list,
            'page_list': get.page_list,
            'admin_page_list': get.admin_page_list,
            'page_list_by_tag_id': get.page_list_by_tag_id
        }

    # IAuthFunctions
    def get_auth_functions(self):
        return {
            'page_create': auth.page_create,
            'page_update': auth.page_update,
            'page_delete': auth.page_delete,
            'page_show': auth.page_show,
            'page_list': auth.page_list,
            'admin_page_list': auth.admin_page_list
        }

    # ITemplateHelpers
    def get_helpers(self):
        return {
            'hdx_events_list': helper.hdx_events_list,
        }

    # IConfigurer
    def update_config(self, config_):
        # toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'hdx_pages')

    # IRoutes
    def before_map(self, map):
        # map.connect('create_page', '/page/new',
        #             controller='ckanext.hdx_pages.controllers.custom_page:PagesController',
        #             action='new',
        #             )
        # map.connect('edit_page', '/page/edit/{id}',
        #             controller='ckanext.hdx_pages.controllers.custom_page:PagesController',
        #             action='edit',
        #             )
        # map.connect('delete_page', '/page/delete/{id}',
        #             controller='ckanext.hdx_pages.controllers.custom_page:PagesController',
        #             action='delete',
        #             )

        # HDX-7859 TO BE commented when search extension is migrated to py3
        # map.connect('read_event', '/event/{id}',
        #             controller='ckanext.hdx_pages.controllers.custom_page:PagesController',
        #             action='read_event',
        #             )
        # map.connect('read_dashboards', '/dashboards/{id}',
        #             controller='ckanext.hdx_pages.controllers.custom_page:PagesController',
        #             action='read_dashboards',
        #             )
        return map

    # IConfigurable
    def configure(self, config):
        pages_model.setup()

# class HdxLightEventPlugin(plugins.SingletonPlugin):
#     plugins.implements(plugins.IBlueprint)
#
#     def get_blueprint(self):
#         return light_page.hdx_light_event
#
#
# class HdxLightDashboardPlugin(plugins.SingletonPlugin):
#     plugins.implements(plugins.IBlueprint)
#
#     def get_blueprint(self):
#         return light_page.hdx_light_dashboard
#
#
# class HdxEventPlugin(plugins.SingletonPlugin):
#     plugins.implements(plugins.IBlueprint)
#
#     def get_blueprint(self):
#         return light_page.hdx_event
#
#
# class HdxDashboardPlugin(plugins.SingletonPlugin):
#     plugins.implements(plugins.IBlueprint)
#
#     def get_blueprint(self):
#         return light_page.hdx_dashboard
