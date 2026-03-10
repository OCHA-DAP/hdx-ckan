"""
reCreated on 19 Sep, 2023

@author: dan
"""

import pytest
import logging as logging
from unittest.mock import patch

from ckanext.hdx_org_group.dao import indicator_access

import ckan.model as model
import ckan.plugins.toolkit as tk
from ckan.types import Context
import ckanext.hdx_org_group.dao.widget_data_service as widget_data_service
from ckanext.hdx_org_group.dao.common_functions import compute_simplifying_units

_get_action = tk.get_action
NotAuthorized = tk.NotAuthorized
NotFound = tk.ObjectNotFound
log = logging.getLogger(__name__)

DUMMY_INDICATOR_DATA = [
    {
        'countryCode': 'ALB',
        'date': '2023-01-01',
        'indicatorTypeName': 'Population',
        'unitName': 'people',
        'sourceName': 'Test Source',
        'datasetLink': 'http://example.com',
        'value': 2800000.0,
    },
    {
        'countryCode': 'ALB',
        'date': '2022-01-01',
        'indicatorTypeName': 'Refugees',
        'unitName': 'people',
        'sourceName': 'UNHCR',
        'datasetLink': 'http://example.com/2',
        'value': 15000.0,
    },
]


@pytest.mark.usefixtures('keep_db_tables_on_clean', 'hdx_clean_db', 'clean_index', 'setup_user_data')
class TestWidgetDataService(object):

    def test_hdx_widget_data_service(self):

        sysadmin_context: Context = {'model': model, 'session': model.Session, 'user': 'testsysadmin'}
        group_dict = _get_action('group_show')(sysadmin_context, {'id': 'some_location'})
        result = widget_data_service.build_widget_data_access(group_dict).get_dataset_results()
        assert isinstance(result, list)

        group_dict['activity_level'] = 'inactive'
        group_dict['name'] = 'alb'

        with patch('ckanext.hdx_org_group.dao.indicator_access.get_action') as mock_get_action:
            mock_get_action.return_value = lambda ctx, data: list(DUMMY_INDICATOR_DATA)

            result = widget_data_service.build_widget_data_access(group_dict).get_dataset_results()
            assert isinstance(result, list)
            assert len(result) > 0

    def test_compute_simplifying_units(self):

        assert compute_simplifying_units(1000000001.0) == 'bln'
        assert compute_simplifying_units(1000001.0) == 'mln'
        assert compute_simplifying_units(1001.0) == 'k'

    def test_indicator_access(self):

        with patch('ckanext.hdx_org_group.dao.indicator_access.get_action') as mock_get_action:
            mock_get_action.return_value = lambda ctx, data: list(DUMMY_INDICATOR_DATA)

            top_line_dao = indicator_access.IndicatorAccess(
                'alb', None, recompute_units=True)

            top_line_data = top_line_dao.fetch_indicator_data_for_country()
            assert len(top_line_data) > 0
