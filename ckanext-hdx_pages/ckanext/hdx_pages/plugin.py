import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit

import ckanext.hdx_pages.actions.create as create


class HdxPagesPlugin(plugins.SingletonPlugin):

    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IRoutes, inherit=True)
    plugins.implements(plugins.IActions, inherit=True)

    def update_config(self, config_):
        # toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'hdx_pages')

    def before_map(self, map):
        map.connect('create_page', '/page/new',
                    controller='ckanext.hdx_pages.controllers.custom_page:PagesController',
                    action='new',
                    )

        return map

    def get_actions(self):
        return {
            'page_create': create.page_create,
        }
