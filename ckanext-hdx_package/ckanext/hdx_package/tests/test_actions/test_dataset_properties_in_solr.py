import json

import ckan.lib.search as search

import ckanext.hdx_theme.tests.hdx_test_with_inds_and_orgs as hdx_test_with_inds_and_orgs


class TestDatasetPropertiesInSolr(hdx_test_with_inds_and_orgs.HDXWithIndsAndOrgsTest):

    def test_dataset_properties_in_solr(self):
        try:
            search_result = search.show('test_private_dataset_1')
        except Exception, e:
            assert False, 'search query needs to succeed'


        package_json = search_result['validated_data_dict']
        package_dict = json.loads(package_json)

        assert 'last_modified' in package_dict
        assert 'has_showcases' in package_dict
        assert 'has_geodata' in package_dict
        assert 'has_quickcharts' in package_dict
        assert 'pageviews_last_14_days' in package_dict
        assert 'total_res_downloads' in package_dict
