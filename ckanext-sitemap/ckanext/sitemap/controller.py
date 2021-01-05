'''
Controller for sitemap
'''
import logging

import math
from lxml import etree
from sqlalchemy.orm import joinedload
from pylons import config, response
from pylons.decorators.cache import beaker_cache

from ckan.lib.base import BaseController
from ckan.lib.helpers import url_for
from ckan.model import Session, Package
from ckan.plugins import toolkit

get_action = toolkit.get_action

SITEMAP_NS = "http://www.sitemaps.org/schemas/sitemap/0.9"

log = logging.getLogger(__file__)

class SitemapController(BaseController):

    ROWS_ON_PAGE = 25

    @beaker_cache(expire=3600*24, type="dbm", invalidate_on_startup=True)
    def _render_sitemap(self, page):
        """
        Build the XML
        """
        datasets = self._search_for_datasets(int(page))

        root = etree.Element("urlset", nsmap={None: SITEMAP_NS})
        for dataset in datasets:
            url = etree.SubElement(root, 'url')
            loc = etree.SubElement(url, 'loc')
            pkg_url = url_for(controller='package', action="read", id = dataset['name'])
            loc.text = config.get('ckan.site_url') + pkg_url
            lastmod = etree.SubElement(url, 'lastmod')
            try:
                modified = dataset.get('metadata_modified')
                if modified:
                    lastmod.text = modified[:10]
            except:
                pass

            for resource in dataset.get('resources', []):
                url = etree.SubElement(root, 'url')
                loc = etree.SubElement(url, 'loc')
                loc.text = config.get('ckan.site_url') + url_for(controller="package", action="resource_read", id = dataset['name'], resource_id = resource['id'])
                lastmod = etree.SubElement(url, 'lastmod')
                try:
                    last_updated = resource.get('last_modified')
                    lastmod.text = last_updated[:10]
                except:
                    pass
        response.headers['Content-type'] = 'text/xml'
        return etree.tostring(root, pretty_print=True)

    def _search_for_datasets(self, page):
        '''
        :param page:
        :type page: int
        :return: list of dataset dicts
        :rtype: list of dict
        '''
        data_dict = {
            'rows': SitemapController.ROWS_ON_PAGE,
            'q': u'',
            'start': (page-1) * SitemapController.ROWS_ON_PAGE,
        }
        result = get_action('package_search')({}, data_dict)
        return result['results']

    def _total_num_of_datasets(self):
        '''
        :param page:
        :type page: int
        :return: list of dataset dicts
        :rtype: list of dict
        '''
        data_dict = {
            'rows': 1,
            'q': u'',
        }
        result = get_action('package_search')({}, data_dict)
        return result['count']

    def view(self):
        """
        List datasets 25 at a time
        """
        #Sitemap Index

        root = etree.Element("sitemapindex", nsmap={None: SITEMAP_NS})
        pkgs = self._total_num_of_datasets()
        count = 1
        if pkgs > 0:
            count = ((pkgs-1) / SitemapController.ROWS_ON_PAGE) + 1
        for i in range(1, count+1):
            sitemap = etree.SubElement(root, 'sitemap')
            loc = etree.SubElement(sitemap, 'loc')
            loc.text = config.get('ckan.site_url') + url_for(controller="ckanext.sitemap.controller:SitemapController", action="index", page=i)
        response.headers['Content-type'] = 'text/xml'
        return etree.tostring(root, pretty_print=True)
        #.limit() and .offset()
        #return self._render_sitemap()

    def index(self, page):
        """
        Create an index of all xml pages
        """
        return self._render_sitemap(page)
