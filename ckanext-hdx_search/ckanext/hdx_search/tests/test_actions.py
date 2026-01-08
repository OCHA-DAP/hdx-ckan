import pytest
from unittest.mock import MagicMock, patch
import ckan.plugins.toolkit as tk
import ckanext.hdx_theme.tests.hdx_test_with_inds_and_orgs as hdx_test_with_inds_and_orgs
from ckan.types import Context
from ckanext.hdx_search.actions.actions import hdx_search_by_object


class TestHdxSearchByObject(hdx_test_with_inds_and_orgs.HDXWithIndsAndOrgsTest):
    @patch('ckanext.hdx_search.actions.actions.hdx_supports_notifications')
    def test_hdx_search_by_object_dataset_with_notifications(self, mock_notifications):
        """Test hdx_search_by_object with dataset object_type when notifications enabled"""
        context: Context = {'ignore_auth': True}
        dataset = tk.get_action('package_show')(context, {'id': 'test_dataset_1'})

        mock_notifications.return_value = True
        data_dict = {'object_type': 'dataset', 'object_id': dataset['id']}

        result = hdx_search_by_object(context, data_dict)

        assert len(result) == 1
        assert result[0]['id'] == dataset['id']
        mock_notifications.assert_called_once_with('dataset', dataset['id'], dataset)

    @patch('ckanext.hdx_search.actions.actions.hdx_supports_notifications')
    def test_hdx_search_by_object_dataset_without_notifications(self, mock_notifications):
        """Test hdx_search_by_object with dataset object_type when notifications disabled"""
        context: Context = {'ignore_auth': True}
        dataset = tk.get_action('package_show')(context, {'id': 'test_dataset_1'})

        mock_notifications.return_value = False
        data_dict = {'object_type': 'dataset', 'object_id': dataset['id']}

        result = hdx_search_by_object(context, data_dict)

        assert len(result) == 0

    @patch('ckanext.hdx_search.actions.actions.get_action')
    @patch('ckanext.hdx_search.actions.actions.hdx_supports_notifications')
    def test_hdx_search_by_object_organization(self, mock_notifications, mock_get_action):
        """Test hdx_search_by_object with organization object_type"""
        context = {'ignore_auth': True}

        # Create datasets in the org
        dataset1 = tk.get_action('package_show')(context, {'id': 'test_dataset_1'})
        dataset2 = tk.get_action('package_show')(context, {'id': 'test_indicator_2'})
        org = tk.get_action('organization_show')(context, {'id': 'hdx-test-org'})

        mock_notifications.return_value = True

        # Mock hdx_light_group_show
        mock_light_group_show = MagicMock(return_value={'name': 'hdx-test-org', 'id': org['id']})

        # Mock package_search to return datasets
        mock_package_search = MagicMock(return_value={'results': [{'id': dataset1['id']}, {'id': dataset2['id']}]})

        mock_get_action.side_effect = lambda action_name: {
            'hdx_light_group_show': mock_light_group_show,
            'package_search': mock_package_search,
        }[action_name]

        data_dict = {'object_type': 'organization', 'object_id': org['id']}
        result = hdx_search_by_object(context, data_dict)

        assert len(result) == 2
        mock_notifications.assert_called_once()

    @patch('ckanext.hdx_search.actions.actions.get_action')
    def test_hdx_search_by_object_group(self, mock_get_action):
        """Test hdx_search_by_object with group object_type"""
        context = {'ignore_auth': True}

        mock_light_group_show = MagicMock(return_value={'id': 'group123', 'name': 'test_group'})
        mock_package_search = MagicMock(return_value={'results': [{'id': 'dataset1'}, {'id': 'dataset2'}]})

        mock_get_action.side_effect = lambda action_name: {
            'hdx_light_group_show': mock_light_group_show,
            'package_search': mock_package_search,
        }[action_name]

        data_dict = {'object_type': 'group', 'object_id': 'group123'}
        result = hdx_search_by_object(context, data_dict)

        assert len(result) == 2
        assert result[0]['id'] == 'dataset1'
        assert result[1]['id'] == 'dataset2'

    @patch('ckanext.hdx_search.actions.actions.get_action')
    @patch('ckanext.hdx_search.actions.actions.hdx_supports_notifications')
    @patch('ckanext.hdx_pages.helpers.helper._find_dataset_filters')
    @patch('ckanext.hdx_pages.helpers.helper.generate_dataset_results')
    def test_hdx_search_by_object_crisis(self, mock_generate, mock_find_filters, mock_notifications, mock_get_action):
        """Test hdx_search_by_object with crisis object_type"""
        context = {'ignore_auth': True}

        mock_notifications.return_value = True
        mock_find_filters.return_value = {}
        mock_generate.return_value = {'additional_fq': 'crisis_filter'}

        page_dict = {'id': 'crisis123', 'type': 'crisis', 'sections': '[{"type": "data_list", "data_url": "test_url"}]'}

        mock_page_show = MagicMock(return_value=page_dict)
        mock_package_search = MagicMock(return_value={'results': [{'id': 'crisis_dataset1'}]})

        mock_get_action.side_effect = lambda action_name: {
            'page_show': mock_page_show,
            'package_search': mock_package_search,
        }[action_name]

        data_dict = {'object_type': 'crisis', 'object_id': 'crisis123'}
        result = hdx_search_by_object(context, data_dict)

        assert len(result) == 1
        assert result[0]['id'] == 'crisis_dataset1'

    def test_hdx_search_by_object_invalid_type(self):
        """Test hdx_search_by_object raises ValueError for invalid object_type"""
        context = {'ignore_auth': True}
        data_dict = {'object_type': 'invalid_type', 'object_id': 'some_id'}

        with pytest.raises(ValueError, match='Unsupported object_type: invalid_type'):
            hdx_search_by_object(context, data_dict)

    def test_hdx_search_by_object_missing_object_type(self):
        """Test hdx_search_by_object raises error when object_type is missing"""
        context = {'ignore_auth': True}
        data_dict = {'object_id': 'some_id'}

        with pytest.raises(tk.ValidationError):
            hdx_search_by_object(context, data_dict)

    def test_hdx_search_by_object_missing_object_id(self):
        """Test hdx_search_by_object raises error when object_id is missing"""
        context = {'ignore_auth': True}
        data_dict = {'object_type': 'dataset'}

        with pytest.raises(tk.ValidationError):
            hdx_search_by_object(context, data_dict)

    @patch('ckanext.hdx_search.actions.actions.get_action')
    def test_hdx_search_by_object_pagination(self, mock_get_action):
        """Test hdx_search_by_object handles pagination correctly"""
        context = {'ignore_auth': True}

        # Create mock datasets for pagination
        first_page = [{'id': f'dataset{i}'} for i in range(1000)]
        second_page = [{'id': f'dataset{i}'} for i in range(1000, 1500)]

        mock_light_group_show = MagicMock(return_value={'id': 'group123', 'name': 'test_group'})

        # Mock package_search to return multiple pages
        mock_package_search = MagicMock(side_effect=[{'results': first_page}, {'results': second_page}])

        mock_get_action.side_effect = lambda action_name: {
            'hdx_light_group_show': mock_light_group_show,
            'package_search': mock_package_search,
        }[action_name]

        data_dict = {'object_type': 'group', 'object_id': 'group123'}
        result = hdx_search_by_object(context, data_dict)

        assert len(result) == 1500
        assert mock_package_search.call_count == 2

        # Verify pagination parameters
        calls = mock_package_search.call_args_list
        assert calls[0][0][1]['start'] == 0
        assert calls[0][0][1]['rows'] == 1000
        assert calls[1][0][1]['start'] == 1000
        assert calls[1][0][1]['rows'] == 1000
