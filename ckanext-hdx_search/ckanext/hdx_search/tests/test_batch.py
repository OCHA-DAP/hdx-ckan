import pytest
import logging as logging

import ckan.model as model

import ckanext.hdx_theme.helpers.helpers as h
import ckanext.hdx_theme.tests.hdx_test_with_inds_and_orgs as hdx_test_with_inds_and_orgs

log = logging.getLogger(__name__)


class TestBatchResults(hdx_test_with_inds_and_orgs.HDXWithIndsAndOrgsTest):

    def test_results_are_batched(self):
        context = {
            'model': model,
            'session': model.Session,
            'user': 'testsysadmin'
        }
        data_dict1 = {
            'id': 'test_dataset_1',
            'batch': 'TEST_BATCH_ID'
        }
        data_dict2 = {
            'id': 'test_indicator_1',
            'batch': 'TEST_BATCH_ID'
        }
        self._get_action('package_patch')(context, data_dict1)
        self._get_action('package_patch')(context, data_dict2)

        url = h.url_for('simple_search')
        result = self.app.get(url)
        assert 'Show 2 other updates from' in result.data

        url_mobile = h.url_for('hdx_light_search.search')

        # we need a test client that doesn't redirect automatically. We want to make sure
        test_client = self.get_backwards_compatible_test_client()
        headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 8.0.0; Pixel 2 XL Build/OPD1.170816.004) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.87 Mobile Safari/537.36'
        }
        result_mobile = test_client.get(url_mobile, headers=headers)
        assert 'Show 2 other updates from' in result_mobile.data
