'''
Created on Nov 12, 2014

@author: alexandru-m-g
'''

import ckan.lib.helpers as h

import ckanext.hdx_theme.tests.hdx_test_base as hdx_test_base
import ckanext.hdx_theme.tests.hdx_test_util as hdx_test_util


class TestBreadcrumbs(hdx_test_base.HdxBaseTest):

    @classmethod
    def _load_plugins(cls):
        hdx_test_base.load_plugin(
            'hdx_search hdx_package hdx_theme')

    def test_breadcrumb_on_search_page(self):
        url = h.url_for(
            controller='ckanext.hdx_search.controllers.search_controller:HDXSearchController', action='search')
        result = self.app.get(url)
        page = str(result.response)

        begin_str = '<ol class="breadcrumb">'
        end_str = '</ol>'
        search_strings = ['<a href="/search">Search</a>']

        hdx_test_util.are_strings_in_text(
            page, search_strings, begin_str, end_str)

    def test_breadcrumb_on_dataset_page(self):
        url = h.url_for(
            controller='ckanext.hdx_search.controllers.simple_search_controller:HDXSimpleSearchController', action='package_search')
        result = self.app.get(url)
        page = str(result.response)

        begin_str = '<ol class="breadcrumb">'
        end_str = '</ol>'
        search_strings = ['<a href="/dataset">Datasets</a>']

        hdx_test_util.are_strings_in_text(
            page, search_strings, begin_str, end_str)
