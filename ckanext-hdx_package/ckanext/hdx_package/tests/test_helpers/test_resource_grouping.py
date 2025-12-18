import pytest
from unittest.mock import patch, Mock

from ckanext.hdx_package.helpers.resource_grouping import (
    set_show_groupings_flag,
    add_other_grouping_if_needed,
    OTHER_MENU_LABEL,
)


class TestSetShowGroupingsFlag:
    @patch('ckanext.hdx_package.helpers.resource_grouping.COD_VALUES_MAP')
    def test_set_show_groupings_flag_with_cod_and_grouping(self, mock_cod_map):
        """Test flag is set when COD level indicates COD and grouping exists"""
        mock_cod_map.get.return_value = {'is_cod': True}

        dataset_dict = {
            'cod_level': 'cod-standard',
            'x_resource_grouping': ['Group A', 'Group B'],
        }

        set_show_groupings_flag(dataset_dict)

        # The function sets x_show_grouping to the grouping list itself when conditions are met
        assert 'x_show_grouping' in dataset_dict
        assert dataset_dict['x_show_grouping'] == ['Group A', 'Group B']
        mock_cod_map.get.assert_called_once_with('cod-standard')

    @patch('ckanext.hdx_package.helpers.resource_grouping.COD_VALUES_MAP')
    def test_set_show_groupings_flag_with_cod_but_no_grouping(self, mock_cod_map):
        """Test flag is set to None when COD level indicates COD but no grouping"""
        mock_cod_map.get.return_value = {'is_cod': True}

        dataset_dict = {
            'cod_level': 'cod-standard',
            'x_resource_grouping': None,
        }

        set_show_groupings_flag(dataset_dict)

        assert dataset_dict['x_show_grouping'] is None

    @patch('ckanext.hdx_package.helpers.resource_grouping.COD_VALUES_MAP')
    def test_set_show_groupings_flag_with_non_cod(self, mock_cod_map):
        """Test flag is set to False when COD level indicates non-COD"""
        mock_cod_map.get.return_value = {'is_cod': False}

        dataset_dict = {
            'cod_level': 'non-cod',
            'x_resource_grouping': ['Group A'],
        }

        set_show_groupings_flag(dataset_dict)

        assert dataset_dict['x_show_grouping'] is False

    @patch('ckanext.hdx_package.helpers.resource_grouping.COD_VALUES_MAP')
    def test_set_show_groupings_flag_without_cod_level(self, mock_cod_map):
        """Test flag is not set when no COD level"""
        dataset_dict = {
            'x_resource_grouping': ['Group A'],
        }

        set_show_groupings_flag(dataset_dict)

        assert 'x_show_grouping' not in dataset_dict
        mock_cod_map.get.assert_not_called()

    @patch('ckanext.hdx_package.helpers.resource_grouping.COD_VALUES_MAP')
    def test_set_show_groupings_flag_with_empty_grouping_list(self, mock_cod_map):
        """Test flag is set to empty list when grouping list is empty"""
        mock_cod_map.get.return_value = {'is_cod': True}

        dataset_dict = {
            'cod_level': 'cod-standard',
            'x_resource_grouping': [],
        }

        set_show_groupings_flag(dataset_dict)

        assert dataset_dict['x_show_grouping'] == []

    @patch('ckanext.hdx_package.helpers.resource_grouping.COD_VALUES_MAP')
    def test_set_show_groupings_flag_cod_map_returns_none(self, mock_cod_map):
        """Test raises AttributeError when COD_VALUES_MAP returns None"""
        mock_cod_map.get.return_value = None

        dataset_dict = {
            'cod_level': 'unknown-level',
            'x_resource_grouping': ['Group A'],
        }

        with pytest.raises(AttributeError, match="'NoneType' object has no attribute 'get'"):
            set_show_groupings_flag(dataset_dict)

    @patch('ckanext.hdx_package.helpers.resource_grouping.COD_VALUES_MAP')
    def test_set_show_groupings_flag_cod_map_missing_is_cod_key(self, mock_cod_map):
        """Test sets flag to None when COD map entry doesn't have is_cod key"""
        mock_cod_map.get.return_value = {'some_other_key': 'value'}

        dataset_dict = {
            'cod_level': 'cod-standard',
            'x_resource_grouping': ['Group A'],
        }

        # .get('is_cod') returns None, and None evaluates to None in 'and' expression
        set_show_groupings_flag(dataset_dict)

        assert dataset_dict['x_show_grouping'] is None

    @patch('ckanext.hdx_package.helpers.resource_grouping.COD_VALUES_MAP')
    def test_set_show_groupings_flag_preserves_grouping_list(self, mock_cod_map):
        """Test that the original grouping list is set as x_show_grouping"""
        mock_cod_map.get.return_value = {'is_cod': True}

        grouping_list = ['health', 'education', 'infrastructure']
        dataset_dict = {
            'cod_level': 'cod-standard',
            'x_resource_grouping': grouping_list,
        }

        set_show_groupings_flag(dataset_dict)

        assert dataset_dict['x_show_grouping'] == grouping_list


class TestAddOtherGroupingIfNeeded:
    def test_add_other_grouping_for_ungrouped_resource(self):
        """Test adds 'Unspecified' grouping for resource without grouping"""
        dataset_dict = {
            'x_resource_grouping': ['Group A', 'Group B'],
            'resources': [
                {'id': 'res1', 'grouping': 'Group A'},
                {'id': 'res2', 'grouping': 'Group C'},  # Not in x_resource_grouping
            ],
        }

        add_other_grouping_if_needed(dataset_dict)

        assert dataset_dict['resources'][0]['x_grouping'] == 'Group A'
        assert dataset_dict['resources'][1]['x_grouping'] == OTHER_MENU_LABEL
        assert OTHER_MENU_LABEL in dataset_dict['x_resource_grouping']
        assert len(dataset_dict['x_resource_grouping']) == 3

    def test_add_other_grouping_all_resources_have_grouping(self):
        """Test no 'Unspecified' added when all resources have valid grouping"""
        dataset_dict = {
            'x_resource_grouping': ['Group A', 'Group B'],
            'resources': [
                {'id': 'res1', 'grouping': 'Group A'},
                {'id': 'res2', 'grouping': 'Group B'},
            ],
        }

        add_other_grouping_if_needed(dataset_dict)

        assert dataset_dict['resources'][0]['x_grouping'] == 'Group A'
        assert dataset_dict['resources'][1]['x_grouping'] == 'Group B'
        assert OTHER_MENU_LABEL not in dataset_dict['x_resource_grouping']
        assert len(dataset_dict['x_resource_grouping']) == 2

    def test_add_other_grouping_multiple_ungrouped_resources(self):
        """Test adds 'Unspecified' only once for multiple ungrouped resources"""
        dataset_dict = {
            'x_resource_grouping': ['Group A'],
            'resources': [
                {'id': 'res1', 'grouping': 'Group A'},
                {'id': 'res2', 'grouping': 'Group X'},
                {'id': 'res3', 'grouping': 'Group Y'},
            ],
        }

        add_other_grouping_if_needed(dataset_dict)

        assert dataset_dict['resources'][0]['x_grouping'] == 'Group A'
        assert dataset_dict['resources'][1]['x_grouping'] == OTHER_MENU_LABEL
        assert dataset_dict['resources'][2]['x_grouping'] == OTHER_MENU_LABEL
        assert dataset_dict['x_resource_grouping'].count(OTHER_MENU_LABEL) == 1
        assert len(dataset_dict['x_resource_grouping']) == 2

    def test_add_other_grouping_empty_resources(self):
        """Test handles empty resources list"""
        dataset_dict = {
            'x_resource_grouping': ['Group A'],
            'resources': [],
        }

        add_other_grouping_if_needed(dataset_dict)

        assert OTHER_MENU_LABEL not in dataset_dict['x_resource_grouping']

    def test_add_other_grouping_no_resources_key(self):
        """Test handles missing resources key"""
        dataset_dict = {
            'x_resource_grouping': ['Group A'],
        }

        add_other_grouping_if_needed(dataset_dict)

        assert OTHER_MENU_LABEL not in dataset_dict['x_resource_grouping']

    def test_add_other_grouping_resource_without_grouping_key(self):
        """Test handles resource without grouping key"""
        dataset_dict = {
            'x_resource_grouping': ['Group A'],
            'resources': [
                {'id': 'res1', 'grouping': 'Group A'},
                {'id': 'res2'},  # No grouping key
            ],
        }

        add_other_grouping_if_needed(dataset_dict)

        assert dataset_dict['resources'][0]['x_grouping'] == 'Group A'
        assert dataset_dict['resources'][1]['x_grouping'] == OTHER_MENU_LABEL
        assert OTHER_MENU_LABEL in dataset_dict['x_resource_grouping']

    def test_add_other_grouping_empty_grouping_list(self):
        """Test handles empty x_resource_grouping list"""
        dataset_dict = {
            'x_resource_grouping': [],
            'resources': [
                {'id': 'res1', 'grouping': 'Group A'},
            ],
        }

        add_other_grouping_if_needed(dataset_dict)

        assert dataset_dict['resources'][0]['x_grouping'] == OTHER_MENU_LABEL
        assert OTHER_MENU_LABEL in dataset_dict['x_resource_grouping']
        assert len(dataset_dict['x_resource_grouping']) == 1

    def test_add_other_grouping_preserves_existing_x_grouping(self):
        """Test sets x_grouping for all resources, both matched and unmatched"""
        dataset_dict = {
            'x_resource_grouping': ['Group A'],
            'resources': [
                {'id': 'res1', 'grouping': 'Group A'},
                {'id': 'res2', 'grouping': 'Group B'},
            ],
        }

        add_other_grouping_if_needed(dataset_dict)

        assert 'x_grouping' in dataset_dict['resources'][0]
        assert 'x_grouping' in dataset_dict['resources'][1]

    def test_add_other_grouping_none_grouping_value(self):
        """Test handles resource with None as grouping value"""
        dataset_dict = {
            'x_resource_grouping': ['Group A'],
            'resources': [
                {'id': 'res1', 'grouping': 'Group A'},
                {'id': 'res2', 'grouping': None},
            ],
        }

        add_other_grouping_if_needed(dataset_dict)

        assert dataset_dict['resources'][0]['x_grouping'] == 'Group A'
        assert dataset_dict['resources'][1]['x_grouping'] == OTHER_MENU_LABEL
        assert OTHER_MENU_LABEL in dataset_dict['x_resource_grouping']
