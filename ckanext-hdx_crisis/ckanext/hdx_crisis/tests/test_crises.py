'''
Created on June 24, 2015

@author: Dan


'''
import logging as logging
import ckan.model as model
import ckan.plugins as p

import ckanext.hdx_theme.tests.hdx_test_base as hdx_test_base
import ckanext.hdx_theme.tests.hdx_test_with_inds_and_orgs as hdx_test_with_inds_and_orgs
import ckanext.hdx_theme.tests.hdx_test_util as hdx_test_util
import ckanext.hdx_crisis.controllers.custom_location_controller as custom_location_controller

log = logging.getLogger(__name__)
extras = [
    {
        'value': '1',
        'key': 'custom_loc',
        'state': 'active'
    }
]

CUSTOM_GROUPS = [
    {
        'name': 'ebola',
        'title': 'Ebola',
        'description': 'This is a Ebola crisis group',
        'extras': extras
    },
    {
        'name': 'mli',
        'title': 'Mali',
        'description': 'This is a Mali group',
        'extras': extras
    },
    {
        'name': 'test-nepal-earthquake-123',
        'title': 'Test Nepal Earthquake 123',
        'description': 'This is Test Nepal Earthquake group page',
        'extras': extras
    },
    {
        'name': 'afg',
        'title': 'Afghanistan',
        'description': 'This is a Afghanistan group',
    },
    {
        "name": "nepal-earthquake",
        'description': "This will be a placeholder for all information related to the earthquake in Nepal.",
        'title': "Nepal Earthquake",
        'extras': [
            {
                "value": "1",
                "state": "active",
                "key": "custom_loc"},
            {
                "value": "{\"topline_resource\":\"a699046b-db5d-4399-b75b-514e351f0975\",\"charts\":[{\"resources\":[{\"chart_dataset_id\":\"\",\"chart_resource_id\":\"\",\"chart_source\":\"\",\"chart_data_link_url\":\"\",\"chart_label\":\"\",\"chart_x_column\":\"\",\"chart_y_column\":\"\"},{}],\"chart_title\":\"\",\"chart_type\":\"bar chart\",\"chart_x_label\":\"\",\"chart_y_label\":\"\"},{\"resources\":[{\"chart_dataset_id\":\"\",\"chart_resource_id\":\"\",\"chart_source\":\"\",\"chart_data_link_url\":\"\",\"chart_label\":\"\",\"chart_x_column\":\"\",\"chart_y_column\":\"\"},{}],\"chart_title\":\"\",\"chart_type\":\"bar chart\",\"chart_x_label\":\"\",\"chart_y_label\":\"\"}],\"map\":{\"map_title\":\"Deaths\",\"map_datatype_1\":\"datastore\",\"map_dataset_id_1\":\"json-repository\",\"map_resource_id_1\":\"60804d36-b0b6-4d1f-9531-bf8f064497df\",\"map_column_1\":\"ocha_pcode\",\"map_values\":\"deaths\",\"map_threshold\":\"1,10,100,1000,2000\",\"map_datatype_2\":\"filestore\",\"map_dataset_id_2\":\"json-repository\",\"map_resource_id_2\":\"b0aa9065-eadb-49ac-8c61-9ffccf4397bc\",\"map_column_2\":\"OCHA_PCODE\",\"map_district_name_column\":\"DISTRICT\"}}",
                "state": "active",
                "key": "customization"},
        ],
    }

]


class TestHDXSearch(hdx_test_with_inds_and_orgs.HDXWithIndsAndOrgsTest):
    @classmethod
    def _load_plugins(cls):
        try:
            hdx_test_base.load_plugin('hdx_crisis hdx_org_group hdx_theme')
        except Exception as e:
            log.warn('Module already loaded')
            log.info(str(e))

    @classmethod
    def _create_test_data(cls):
        super(TestHDXSearch, cls)._create_test_data()
        cls._create_crises()

    def test_is_custom(self):
        custom_group = {'id': 'nepal-earthquake'}
        regular_group = {'id': 'afg'}
        assert True == custom_location_controller.is_custom(None, custom_group)
        assert False == custom_location_controller.is_custom(None, regular_group)

    def test_crises(self):
        context = {'ignore_auth': True,
                   'model': model, 'session': model.Session, 'user': 'testsysadmin'}
        result = self._get_action('group_list')(context, {})

        # in total should be 7 created groups
        assert 7 == len(result)

        # count number of created crises
        no_crises = sum(
            1 for group in CUSTOM_GROUPS if custom_location_controller.is_custom(None, {'id': group['name']}))
        assert 4 == no_crises

    @classmethod
    def _create_crises(cls):
        for group in CUSTOM_GROUPS:
            context = {'ignore_auth': True,
                       'model': model, 'session': model.Session, 'user': 'testsysadmin'}
            cls._get_action('group_create')(context, group)
