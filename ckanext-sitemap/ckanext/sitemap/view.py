import logging

from flask import Blueprint, make_response
from lxml import etree

import ckan.plugins.toolkit as tk

get_action = tk.get_action
check_access = tk.check_access
render = tk.render
abort = tk.abort
_ = tk._
url_for = tk.url_for
config = tk.config

ROWS_ON_PAGE = 25
SITEMAP_NS = "http://www.sitemaps.org/schemas/sitemap/0.9"

log = logging.getLogger(__file__)

sitemap = Blueprint(u'sitemap', __name__)


def _render_sitemap(page):
    """
    Build the XML
    """

    try:
        t = int(page)
    except:
        abort(404, _('Page not found'))

    datasets = _search_for_datasets(int(page))

    root = etree.Element("urlset", nsmap={None: SITEMAP_NS})
    for dataset in datasets:
        url = etree.SubElement(root, 'url')
        loc = etree.SubElement(url, 'loc')
        pkg_url = url_for('dataset_read', id=dataset['name'])
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
            loc.text = config.get('ckan.site_url') + url_for('resource_read', id=dataset['name'], resource_id=resource['id'])
            try:
                last_updated = resource.get('last_modified')
                if last_updated:
                    lastmod = etree.SubElement(url, 'lastmod')
                    lastmod.text = last_updated[:10]
            except:
                pass
    response_text = etree.tostring(root, pretty_print=True)
    response = make_response(response_text)
    response.headers['Content-type'] = 'text/xml'
    return response


def _search_for_datasets(page):
    '''
    :param page:
    :type page: int
    :return: list of dataset dicts
    :rtype: list of dict
    '''
    data_dict = {
        'rows': ROWS_ON_PAGE,
        'q': u'',
        'start': (page-1) * ROWS_ON_PAGE,
    }
    result = get_action('package_search')({}, data_dict)
    return result['results']


def _total_num_of_datasets():
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


def view():
    """
    List datasets 25 at a time
    """
    #Sitemap Index

    root = etree.Element("sitemapindex", nsmap={None: SITEMAP_NS})
    pkgs = _total_num_of_datasets()
    count = 1
    if pkgs > 0:
        count = ((pkgs-1) // ROWS_ON_PAGE) + 1
    for i in range(1, count+1):
        sitemap = etree.SubElement(root, 'sitemap')
        loc = etree.SubElement(sitemap, 'loc')
        loc.text = config.get('ckan.site_url') + url_for('sitemap.index', page=i)

    response_text = etree.tostring(root, pretty_print=True)
    response = make_response(response_text)
    response.headers['Content-type'] = 'text/xml'
    return response


def index(page):
    """
    Create an index of all xml pages
    """
    return _render_sitemap(page)


sitemap.add_url_rule(u'/sitemap.xml', view_func=view)
sitemap.add_url_rule(u'/sitemap<page>.xml', view_func=index)
