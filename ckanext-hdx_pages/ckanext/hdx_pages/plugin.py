import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit

import ckanext.hdx_pages.actions.create as create
import ckanext.hdx_pages.actions.delete as delete
import ckanext.hdx_pages.actions.update as update
import ckanext.hdx_pages.actions.get as get
import ckanext.hdx_pages.actions.auth as auth

import ckanext.hdx_pages.helpers.helper as helper


class HdxPagesPlugin(plugins.SingletonPlugin):

    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IRoutes, inherit=True)
    plugins.implements(plugins.IActions, inherit=True)
    plugins.implements(plugins.IAuthFunctions, inherit=True)
    plugins.implements(plugins.ITemplateHelpers)

    def update_config(self, config_):
        # toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'hdx_pages')

    def before_map(self, map):
        map.connect('create_page', '/page/new',
                    controller='ckanext.hdx_pages.controllers.custom_page:PagesController',
                    action='new',
                    )
        map.connect('edit_page', '/page/edit/{id}',
                    controller='ckanext.hdx_pages.controllers.custom_page:PagesController',
                    action='edit',
                    )
        map.connect('delete_page', '/page/delete/{id}',
                    controller='ckanext.hdx_pages.controllers.custom_page:PagesController',
                    action='delete',
                    )
        map.connect('read_event', '/event/{id}',
                    controller='ckanext.hdx_pages.controllers.custom_page:PagesController',
                    action='read_event',
                    )
        map.connect('read_dashboards', '/dashboards/{id}',
                    controller='ckanext.hdx_pages.controllers.custom_page:PagesController',
                    action='read_dashboards',
                    )
        return map

    def get_actions(self):
        return {
            'page_create': create.page_create,
            'page_delete': delete.page_delete,
            'page_update': update.page_update,
            'page_show': get.page_show,
            'page_group_list': get.page_group_list,
            'group_page_list': get.group_page_list,
            'page_list': get.page_list
        }

    def get_auth_functions(self):
        return {
            'page_create': auth.page_create,
            'page_update': auth.page_update,
            'page_delete': auth.page_delete,
            'page_show': auth.page_show
        }

    def get_helpers(self):
        return {
            'hdx_events_list': helper.hdx_events_list,
        }