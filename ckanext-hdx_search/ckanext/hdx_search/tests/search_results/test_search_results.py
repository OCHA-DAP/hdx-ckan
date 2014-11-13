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
    indicator_counts = c.indicator_counts
    dataset_counts = c.dataset_counts
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
        assert dataset_counts == 1, '1 datasets'

        # Testing search on indicators tab
        url = h.url_for(
            'search', q='hdxtest', ext_indicator='1')
        self.app.get(url)

        assert indicator_counts == 2, '2 indicator'
        assert dataset_counts == 1, '1 datasets'

        search_controller.HDXSearchController._performing_search = performing_search_original
