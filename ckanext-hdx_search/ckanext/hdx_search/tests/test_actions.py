# import pytest
# from unittest.mock import Mock, patch
#
#
# class TestHdxSearchByObject:
#     """Test class for hdx_search_by_object action."""
#
#     @pytest.fixture
#     def mock_context(self):
#         """Mock context for action calls."""
#         return {'user': 'test_user', 'model': Mock()}
#
#     @pytest.fixture
#     def mock_get_action(self):
#         """Mock get_action calls."""
#         with patch('ckanext.hdx_search.actions.actions.get_action') as mock:
#             yield mock
#
#     @pytest.fixture
#     def mock_check_access(self):
#         """Mock _check_access calls."""
#         with patch('ckanext.hdx_search.actions.actions._check_access') as mock:
#             yield mock
#
#     @pytest.fixture
#     def mock_hdx_supports_notifications(self):
#         """Mock hdx_supports_notifications helper."""
#         with patch('ckanext.hdx_search.actions.actions.hdx_supports_notifications') as mock:
#             yield mock
#
#     def test_search_by_dataset_with_notifications_enabled(
#         self, mock_context, mock_get_action, mock_check_access, mock_hdx_supports_notifications
#     ):
#         """Test searching by dataset when notifications are enabled."""
#         from ckanext.hdx_search.actions.actions import hdx_search_by_object
#
#         # Setup
#         dataset_id = 'test-dataset-id'
#         mock_hdx_supports_notifications.return_value = True
#         mock_get_action.return_value = Mock(return_value={'id': dataset_id, 'name': 'Test Dataset'})
#
#         data_dict = {'object_type': 'dataset', 'object_id': dataset_id}
#
#         # Execute
#         result = hdx_search_by_object(mock_context, data_dict)
#
#         # Assert
#         mock_check_access.assert_called_once_with('package_search', mock_context, data_dict)
#         assert len(result) == 1
#         assert result[0]['id'] == dataset_id
#
#     def test_search_by_dataset_with_notifications_disabled(
#         self, mock_context, mock_get_action, mock_check_access, mock_hdx_supports_notifications
#     ):
#         """Test searching by dataset when notifications are disabled."""
#         from ckanext.hdx_search.actions.actions import hdx_search_by_object
#
#         # Setup
#         mock_hdx_supports_notifications.return_value = False
#         mock_get_action.return_value = Mock(return_value={'id': 'test-id', 'name': 'Test Dataset'})
#
#         data_dict = {'object_type': 'dataset', 'object_id': 'test-id'}
#
#         # Execute
#         result = hdx_search_by_object(mock_context, data_dict)
#
#         # Assert
#         assert len(result) == 0
#
#     def test_search_by_organization(
#         self, mock_context, mock_get_action, mock_check_access, mock_hdx_supports_notifications
#     ):
#         """Test searching by organization."""
#         from ckanext.hdx_search.actions.actions import hdx_search_by_object
#
#         # Setup
#         org_name = 'test-org'
#         mock_hdx_supports_notifications.return_value = True
#         mock_get_action.side_effect = [
#             Mock(return_value={'id': 'org-id', 'name': org_name}),  # hdx_light_group_show
#             Mock(return_value={'results': [{'id': 'dataset-1'}, {'id': 'dataset-2'}], 'count': 2}),  # package_search
#         ]
#
#         data_dict = {'object_type': 'organization', 'object_id': 'org-id'}
#
#         # Execute
#         result = hdx_search_by_object(mock_context, data_dict)
#
#         # Assert
#         assert len(result) == 2
#         assert result[0]['id'] == 'dataset-1'
#         assert result[1]['id'] == 'dataset-2'
#
#     def test_search_by_group(self, mock_context, mock_get_action, mock_check_access):
#         """Test searching by group."""
#         from ckanext.hdx_search.actions.actions import hdx_search_by_object
#
#         # Setup
#         group_name = 'test-group'
#         mock_get_action.side_effect = [
#             Mock(return_value={'id': 'group-id', 'name': group_name}),  # hdx_light_group_show
#             Mock(return_value={'results': [{'id': 'dataset-1'}], 'count': 1}),  # package_search
#         ]
#
#         data_dict = {'object_type': 'group', 'object_id': 'group-id'}
#
#         # Execute
#         result = hdx_search_by_object(mock_context, data_dict)
#
#         # Assert
#         assert len(result) == 1
#         assert result[0]['id'] == 'dataset-1'
#
#     @patch('ckanext.hdx_search.actions.actions.page_h')
#     def test_search_by_crisis(
#         self, mock_page_h, mock_context, mock_get_action, mock_check_access, mock_hdx_supports_notifications
#     ):
#         """Test searching by crisis."""
#         from ckanext.hdx_search.actions.actions import hdx_search_by_object
#         import json
#
#         # Setup
#         crisis_id = 'crisis-123'
#         mock_hdx_supports_notifications.return_value = True
#
#         sections = [{'type': 'data_list', 'data_url': 'http://example.com/data'}]
#         mock_get_action.side_effect = [
#             Mock(return_value={'id': crisis_id, 'type': 'crisis', 'sections': json.dumps(sections)}),  # page_show
#             Mock(return_value={'results': [{'id': 'dataset-1'}], 'count': 1}),  # package_search
#         ]
#
#         mock_page_h._find_dataset_filters.return_value = {'filter': 'value'}
#         mock_page_h.generate_dataset_results.return_value = {'additional_fq': 'crisis:"test-crisis"'}
#
#         data_dict = {'object_type': 'crisis', 'object_id': crisis_id}
#
#         # Execute
#         result = hdx_search_by_object(mock_context, data_dict)
#
#         # Assert
#         assert len(result) == 1
#         assert result[0]['id'] == 'dataset-1'
#
#     def test_search_with_pagination(self, mock_context, mock_get_action, mock_check_access):
#         """Test searching with pagination."""
#         from ckanext.hdx_search.actions.actions import hdx_search_by_object
#
#         # Setup - simulate 2500 results requiring 3 pages
#         mock_get_action.side_effect = [
#             Mock(return_value={'id': 'group-id', 'name': 'test-group'}),  # hdx_light_group_show
#             Mock(return_value={'results': [{'id': f'dataset-{i}'} for i in range(1000)], 'count': 2500}),  # page 1
#             Mock(
#                 return_value={'results': [{'id': f'dataset-{i}'} for i in range(1000, 2000)], 'count': 2500}
#             ),  # page 2
#             Mock(
#                 return_value={'results': [{'id': f'dataset-{i}'} for i in range(2000, 2500)], 'count': 2500}
#             ),  # page 3
#         ]
#
#         data_dict = {'object_type': 'group', 'object_id': 'group-id'}
#
#         # Execute
#         result = hdx_search_by_object(mock_context, data_dict)
#
#         # Assert
#         assert len(result) == 2500
#         assert result[0]['id'] == 'dataset-0'
#         assert result[2499]['id'] == 'dataset-2499'
#
#     def test_search_with_invalid_object_type(self, mock_context, mock_check_access):
#         """Test searching with invalid object type."""
#         from ckanext.hdx_search.actions.actions import hdx_search_by_object
#
#         data_dict = {'object_type': 'invalid_type', 'object_id': 'some-id'}
#
#         # Execute and assert
#         with pytest.raises(ValueError, match='Unsupported object_type: invalid_type'):
#             hdx_search_by_object(mock_context, data_dict)
#
#     def test_search_with_missing_object_type(self, mock_context, mock_check_access):
#         """Test searching with missing object_type."""
#         from ckanext.hdx_search.actions.actions import hdx_search_by_object
#
#         data_dict = {'object_id': 'some-id'}
#
#         # Execute and assert
#         with pytest.raises(Exception):  # Will raise from _get_or_bust
#             hdx_search_by_object(mock_context, data_dict)
#
#     def test_search_with_missing_object_id(self, mock_context, mock_check_access):
#         """Test searching with missing object_id."""
#         from ckanext.hdx_search.actions.actions import hdx_search_by_object
#
#         data_dict = {'object_type': 'dataset'}
#
#         # Execute and assert
#         with pytest.raises(Exception):  # Will raise from _get_or_bust
#             hdx_search_by_object(mock_context, data_dict)
#
#     def test_search_filters_archived_and_private_datasets(
#         self, mock_context, mock_get_action, mock_check_access, mock_hdx_supports_notifications
#     ):
#         """Test that search properly filters archived and private datasets."""
#         from ckanext.hdx_search.actions.actions import hdx_search_by_object
#
#         # Setup
#         mock_hdx_supports_notifications.return_value = True
#
#         mock_light_group_show = Mock(return_value={'id': 'org-id', 'name': 'test-org'})
#         mock_package_search = Mock(return_value={'results': [], 'count': 0})
#
#         # Return the mock functions themselves, not their return values
#         mock_get_action.side_effect = lambda action: {
#             'hdx_light_group_show': mock_light_group_show,
#             'package_search': mock_package_search,
#         }[action]
#
#         data_dict = {'object_type': 'organization', 'object_id': 'org-id'}
#
#         # Execute
#         hdx_search_by_object(mock_context, data_dict)
#
#         # Assert - check that package_search was called with correct filters
#         mock_package_search.assert_called_once()
#         search_dict = mock_package_search.call_args[0][1]
#
#         assert '-extras_archived:"true"' in search_dict['fq_list']
#         assert '+capacity:"public"' in search_dict['fq_list']
#         assert '+dataset_type:dataset' in search_dict['fq_list']
