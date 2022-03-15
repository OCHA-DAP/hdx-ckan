import pytest

import ckanext.hdx_theme.tests.hdx_test_base as hdx_test_base
import ckanext.hdx_theme.tests.hdx_test_util as hdx_test_util
import ckanext.hdx_theme.tests.hdx_test_with_inds_and_orgs as hdx_test_with_inds_and_orgs

import ckanext.hdx_theme.helpers.helpers as h


class TestBreadcrumbs(hdx_test_with_inds_and_orgs.HDXWithIndsAndOrgsTest):

    @classmethod
    def _load_plugins(cls):
        hdx_test_base.load_plugin(
            'hdx_search hdx_package hdx_theme')

    # def test_breadcrumb_on_search_page(self):
    #     url = h.url_for(
    #         controller='ckanext.hdx_search.controllers.search_controller:HDXSearchController', action='search')
    #     result = self.app.get(url)
    #     page = str(result.response)
    #
    #     begin_str = '<ol class="breadcrumb" vocab="https://schema.org/" typeof="BreadcrumbList">'
    #     end_str = '</ol>'
    #     search_strings = ['<a href="/search">Search</a>']
    #
    #     hdx_test_util.are_strings_in_text(
    #         page, search_strings, begin_str, end_str)

    def test_breadcrumb_on_dataset_page(self):
        url = h.url_for('hdx_dataset.search')
        result = self.app.get(url)
        page = result.body

        begin_str = '<ol class="breadcrumb" vocab="https://schema.org/" typeof="BreadcrumbList">'
        end_str = '</ol>'
        search_strings = ['href="/dataset">Datasets</a>']

        hdx_test_util.are_strings_in_text(page, search_strings, begin_str, end_str)
