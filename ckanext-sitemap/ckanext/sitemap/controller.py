'''
Controller for sitemap
'''
import logging

from ckan.lib.base import BaseController
from ckan.model import Session, Package
from ckan.lib.helpers import url_for
from lxml import etree
from pylons import config, response
from pylons.decorators.cache import beaker_cache

SITEMAP_NS = "http://www.sitemaps.org/schemas/sitemap/0.9"

log = logging.getLogger(__file__)

class SitemapController(BaseController):

    @beaker_cache(expire=3600*24, type="dbm", invalidate_on_startup=True)
    def _render_sitemap(self, page):
        root = etree.Element("urlset", nsmap={None: SITEMAP_NS})
        #pkgs = Session.query(Package).all()
        pkgs = Session.query(Package).filter(Package.private == 0).offset(int(page)*25).limit(25)
        for pkg in pkgs:
            url = etree.SubElement(root, 'url')
            loc = etree.SubElement(url, 'loc')
            pkg_url = url_for(controller='package', action="read", id = pkg.name)
            loc.text = config.get('ckan.site_url') + pkg_url
            lastmod = etree.SubElement(url, 'lastmod')
            lastmod.text = pkg.latest_related_revision.timestamp.strftime('%Y-%m-%d')
            for res in pkg.resources:
                url = etree.SubElement(root, 'url')
                loc = etree.SubElement(url, 'loc')
                loc.text = config.get('ckan.site_url') + url_for(controller="package", action="resource_read", id = pkg.name, resource_id = res.id)
                lastmod = etree.SubElement(url, 'lastmod')
                lastmod.text = res.created.strftime('%Y-%m-%d')
        response.headers['Content-type'] = 'text/xml'
        return etree.tostring(root, pretty_print=True)

    def view(self):
        #Sitemap Index
        root = etree.Element("sitemapindex", nsmap={None: SITEMAP_NS})
        pkgs = Session.query(Package).count()
        count = pkgs/25
        for i in range(1,count):
            sitemap = etree.SubElement(root, 'sitemap')
            loc = etree.SubElement(sitemap, 'loc')
            loc.text = config.get('ckan.site_url') + url_for(controller="ckanext.sitemap.controller:SitemapController", action="index", page=i)
        response.headers['Content-type'] = 'text/xml'
        return etree.tostring(root, pretty_print=True)
        #.limit() and .offset()
        #return self._render_sitemap()

    def index(self, page):
        return self._render_sitemap(page)