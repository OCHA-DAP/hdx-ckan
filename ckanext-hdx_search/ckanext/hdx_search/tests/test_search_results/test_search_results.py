'''
Created on Nov 6, 2014

@author: alexandru-m-g
'''
import logging as logging

import ckan.plugins.toolkit as tk
import ckan.model as model
import ckan.lib.helpers as h
import ckan.common as common

import ckanext.hdx_theme.tests.hdx_test_base as hdx_test_base
import ckanext.hdx_theme.tests.hdx_test_with_inds_and_orgs as hdx_test_with_inds_and_orgs
import ckanext.hdx_search.controllers.search_controller as search_controller

c = common.c

log = logging.getLogger(__name__)

indicator_counts = 0
dataset_counts = 0

performing_search_original = search_controller.HDXSearchController._performing_search


def performing_search_wrapper(self, *args):
    global indicator_counts
    global dataset_counts
    ret = performing_search_original(self, *args)
    facet_item_list = c.search_facets.get('indicator', {}).get('items', [])
    indicator_counts = next((item.get('count', 0) for item in facet_item_list if item.get('name', '') == '1'), 0)
    dataset_counts = c.count - indicator_counts
    return ret


search_controller.HDXSearchController._performing_search = performing_search_wrapper


log = logging.getLogger(__name__)


class TestHDXSearchResults(hdx_test_with_inds_and_orgs.HDXWithIndsAndOrgsTest):

    @classmethod
    def _load_plugins(cls):
        hdx_test_base.load_plugin('hdx_search hdx_package hdx_theme')

    def test_hdx_search_results(self):
        global packages

        # Testing search on all tab
        url = h.url_for(
            'search', q='hdxtest')
        self.app.get(url)

        assert indicator_counts == 2, '2 indicator'
        assert dataset_counts == 1, '1 dataset, 3 in total'

        # Testing search with indicator filter
        url = h.url_for(
            'search', q='hdxtest', ext_indicator='1')
        self.app.get(url)

        assert indicator_counts == 2, '2 indicator'
        assert dataset_counts == 0, '0 datasets because of the filter'

        search_controller.HDXSearchController._performing_search = performing_search_original

    def test_search_recommendations(self):
        url = h.url_for(
            controller='ckanext.hdx_search.controllers.search_controller:HDXSearchController', action='search', q='Nepal')
        result = self.app.get(url)
        assert '<div id="search-ahead"' in str(result.response)