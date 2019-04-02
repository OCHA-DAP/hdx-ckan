'''
Created on Nov 12, 2014

@author: alexandru-m-g
'''

import logging as logging

import ckanext.hdx_theme.tests.hdx_test_base as hdx_test_base
import ckanext.hdx_theme.tests.hdx_test_util as hdx_test_util
import ckanext.hdx_theme.tests.hdx_test_with_inds_and_orgs as hdx_test_with_inds_and_orgs

import ckan.lib.helpers as h

log = logging.getLogger(__name__)


class TestBreadcrumbs(hdx_test_with_inds_and_orgs.HDXWithIndsAndOrgsTest):
    @classmethod
    def _load_plugins(cls):
        hdx_test_base.load_plugin('hdx_org_group hdx_users hdx_search hdx_package hdx_theme')

    def test_breadcrumb_on_indicator_page(self):
        url = h.url_for(controller='package', action='read', id='test_indicator_1')
        result = self.app.get(url)
        page = str(result.response)

        begin_str = '<ol class="breadcrumb" vocab="https://schema.org/" typeof="BreadcrumbList">'
        end_str = '</ol>'
        search_strings = ['/dataset', 'Test Indicator 1', 'test_indicator_1']

        hdx_test_util.are_strings_in_text(page, search_strings, begin_str, end_str)

    def test_breadcrumb_on_dataset_page(self):
        url = h.url_for(controller='package', action='read', id='test_dataset_1')
        result = self.app.get(url)
        page = str(result.response)

        begin_str = '<ol class="breadcrumb" vocab="https://schema.org/" typeof="BreadcrumbList">'
        end_str = '</ol>'
        search_strings = ['/dataset', 'Test Dataset 1', 'test_dataset_1']

        hdx_test_util.are_strings_in_text(page, search_strings, begin_str, end_str)
