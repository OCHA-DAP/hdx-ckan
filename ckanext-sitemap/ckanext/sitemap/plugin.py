'''
Sitemap plugin for CKAN
'''

from ckan.plugins import implements, SingletonPlugin
from ckan.plugins import IBlueprint

from ckanext.sitemap.view import sitemap


class SitemapPlugin(SingletonPlugin):
    # implements(IRoutes, inherit=True)
    implements(IBlueprint)

    def get_blueprint(self):
        return sitemap

    def before_map(self, map):
        controller='ckanext.sitemap.controller:SitemapController'
        map.connect('sitemap', '/sitemap.xml', controller=controller, action='view')
        map.connect('sitemap_page', '/sitemap{page}.xml', controller=controller, action='index')
        return map

