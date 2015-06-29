'''
Created on Jun 26, 2015

@author: alexandru-m-g
'''

import logging

import ckanext.hdx_theme.tests.hdx_test_base as hdx_test_base
import ckanext.hdx_theme.tests.hdx_test_with_inds_and_orgs as hdx_test_with_inds_and_orgs
import ckanext.hdx_org_group.controllers.custom_org_controller as controller

log = logging.getLogger(__name__)


class TestMembersController(hdx_test_with_inds_and_orgs.HDXWithIndsAndOrgsTest):

    @classmethod
    def _load_plugins(cls):
        hdx_test_base.load_plugin('hdx_org_group hdx_package hdx_theme')

    @classmethod
    def _create_test_data(cls):
        super(TestMembersController, cls)._create_test_data(create_datasets=False, create_members=True)

    def test_assemble_viz_config(self):
        custom_org_controller = controller.CustomOrgController()

        # Testing the WFP viz part
        json_config = '''
            {
                "visualization-select": "WFP",
                "viz-title": "Test Visualization Title",
                "viz-data-link-url": "https://data.hdx.rwlabs.org/dataset/wfp-food-prices",
                "viz-resource-id": "test-resource-id"
            }
        '''
        config = custom_org_controller.assemble_viz_config(json_config)

        assert config == {
            'title': 'Test Visualization Title',
            'data_link_url': 'https://data.hdx.rwlabs.org/dataset/wfp-food-prices',
            'type': 'WFP',
            'embedded': 'true',
            # 'resource_id': 'test-resource-id',
            'datastore_id': 'test-resource-id'
        }

        # Testing the 3W viz part
        json_config = '''
        {
            "visualization-select": "3W-dashboard",
            "viz-title": "Who's doing what and where ?",
            "viz-data-link-url": "https://data.hdx.rwlabs.org/dataset/3w-matrix-for-somalia-ngo-consortium",
            "datatype_1": "datastore",
            "dataset_id_1": "dataset_id_1",
            "resource_id_1": "1d5b6821-fe99-4a5d-a0cf-d6987868027b",
            "datatype_2": "filestore",
            "dataset_id_2": "json-repository",
            "resource_id_2": "07c835cd-7b47-4d76-97e0-ff0fd5cc09c5",
            "map_district_name_column": "DIST_NAME",
            "where-column": "DIST_NO",
            "where-column-2": "DIS_CODE",
            "who-column": "Organisation",
            "what-column": "Sector",
            "colors": ["red", "green", "blue"]
        }
        '''

        config = custom_org_controller.assemble_viz_config(json_config)

        assert config, 'Config dict should not be empty'
        assert config == {
            'type': '3W-dashboard',
            'title': "Who's doing what and where ?",
            'geotype': 'filestore',
            'geo': '/dataset/json-repository/resource_download/07c835cd-7b47-4d76-97e0-ff0fd5cc09c5',
            'data_link_url': 'https://data.hdx.rwlabs.org/dataset/3w-matrix-for-somalia-ngo-consortium',
            'data': '/api/action/datastore_search?resource_id=1d5b6821-fe99-4a5d-a0cf-d6987868027b&limit=10000000',
            'datatype': 'datastore',
            'joinAttribute': 'DIS_CODE',
            'whereFieldName': 'DIST_NO',
            'whoFieldName': 'Organisation',
            'whatFieldName': 'Sector',
            'nameAttribute': 'DIST_NAME',
            'colors': ["red", "green", "blue"]
        }
