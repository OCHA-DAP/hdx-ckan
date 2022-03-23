import pytest
import logging as logging


import ckanext.hdx_theme.helpers.helpers as h

import ckanext.hdx_theme.tests.hdx_test_base as hdx_test_base
import ckanext.hdx_theme.tests.hdx_test_with_inds_and_orgs as hdx_test_with_inds_and_orgs
import ckanext.hdx_search.controller_logic.search_logic as search_logic


log = logging.getLogger(__name__)

dataset_counts = 0

prepare_facets_info_original = search_logic.SearchLogic._prepare_facets_info


def prepare_facet_info_wrapper(self, *args, **kwargs):
    global indicator_counts
    global dataset_counts
    ret = prepare_facets_info_original(self, *args, **kwargs)
    dataset_counts = ret.get('num_of_total_items')
    return ret


class TestHDXSearchResults(hdx_test_with_inds_and_orgs.HDXWithIndsAndOrgsTest):

    @classmethod
    def setup_class(cls):
        super(TestHDXSearchResults, cls).setup_class()
        search_logic.SearchLogic._prepare_facets_info = prepare_facet_info_wrapper

    @classmethod
    def teardown_class(cls):
        super(TestHDXSearchResults, cls).teardown_class()
        search_logic.SearchLogic._prepare_facets_info = prepare_facets_info_original

    @classmethod
    def _load_plugins(cls):
        hdx_test_base.load_plugin('hdx_search hdx_package hdx_theme')

    def test_hdx_search_results(self):
        # Testing search on all tab
        url = h.url_for('hdx_dataset.search', q='hdxtest')
        self.app.get(url)

        assert dataset_counts == 3, '3 datasets in total'

    def test_search_recommendations(self):
        url = h.url_for('hdx_search.search', q='Nepal')
        result = self.app.get(url)
        assert '<div class="search-ahead"' in result.body
