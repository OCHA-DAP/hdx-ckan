import pytest
from unittest.mock import Mock, patch

from ckanext.hdx_package.controller_logic.contribute_flow_write_logic import ContributeFlowWriteLogic
import ckanext.hdx_package.helpers.custom_validator as vd


class TestContributeFlowWriteLogic:
    @pytest.fixture
    def sample_dataset_dict(self):
        """Sample dataset dictionary for testing"""
        return {
            'name': 'test-dataset',
            'title': 'Test Dataset',
            'notes': 'Test description',
            'tag_string': 'tag1, tag2',
            'locations': ['country1', 'country2'],
            'maintainer': 'test_user',
            'private': 'public',
        }

    @pytest.fixture
    def mock_context(self):
        """Mock context for CKAN operations"""
        return {'model': Mock(), 'session': Mock(), 'user': 'test_user'}

    def test_init(self, sample_dataset_dict):
        """Test initialization of ContributeFlowWriteLogic"""
        logic = ContributeFlowWriteLogic(sample_dataset_dict)
        assert logic.dataset_dict == sample_dataset_dict

    def test_process_tag_string_empty(self):
        """Test process_tag_string when tag_string is missing"""
        dataset_dict = {'name': 'test'}
        logic = ContributeFlowWriteLogic(dataset_dict)

        logic.process_tag_string()

        assert logic.dataset_dict['tag_string'] == ''
        assert logic.dataset_dict['tags'] == []

    def test_process_tag_string_existing(self):
        """Test process_tag_string when tag_string already exists"""
        dataset_dict = {'name': 'test', 'tag_string': 'tag1, tag2'}
        logic = ContributeFlowWriteLogic(dataset_dict)

        logic.process_tag_string()

        assert logic.dataset_dict['tag_string'] == 'tag1, tag2'

    def test_process_locations_single_string(self):
        """Test process_locations with a single location string"""
        dataset_dict = {'locations': 'country1'}
        logic = ContributeFlowWriteLogic(dataset_dict)

        logic.process_locations()

        assert logic.dataset_dict['groups'] == [{'name': 'country1'}]

    def test_process_locations_list(self):
        """Test process_locations with a list of locations"""
        dataset_dict = {'locations': ['country1', 'country2', 'country3']}
        logic = ContributeFlowWriteLogic(dataset_dict)

        logic.process_locations()

        expected_groups = [{'name': 'country1'}, {'name': 'country2'}, {'name': 'country3'}]
        assert logic.dataset_dict['groups'] == expected_groups

    def test_process_locations_empty(self):
        """Test process_locations with no locations"""
        dataset_dict = {'name': 'test'}
        logic = ContributeFlowWriteLogic(dataset_dict)

        logic.process_locations()

        assert logic.dataset_dict['groups'] == []

    def test_process_dataset_date_both_ranges(self):
        """Test process_dataset_date with both date ranges"""
        dataset_dict = {'date_range1': '2020-01-01', 'date_range2': '2020-12-31'}
        logic = ContributeFlowWriteLogic(dataset_dict)

        logic.process_dataset_date()

        assert logic.dataset_dict['dataset_date'] == '[2020-01-01 TO 2020-12-31]'

    def test_process_dataset_date_only_start(self):
        """Test process_dataset_date with only start date"""
        dataset_dict = {'date_range1': '2020-01-01'}
        logic = ContributeFlowWriteLogic(dataset_dict)

        logic.process_dataset_date()

        assert logic.dataset_dict['dataset_date'] == '[2020-01-01 TO *]'

    def test_process_dataset_date_only_end(self):
        """Test process_dataset_date with only end date"""
        dataset_dict = {'date_range2': '2020-12-31'}
        logic = ContributeFlowWriteLogic(dataset_dict)

        logic.process_dataset_date()

        assert logic.dataset_dict['dataset_date'] == '[* TO 2020-12-31]'

    def test_process_dataset_date_no_dates(self):
        """Test process_dataset_date with no date ranges"""
        dataset_dict = {'name': 'test'}
        logic = ContributeFlowWriteLogic(dataset_dict)

        logic.process_dataset_date()

        assert 'dataset_date' not in logic.dataset_dict

    def test_process_expected_update_frequency_default(self):
        """Test process_expected_update_frequency with default value"""
        dataset_dict = {'data_update_frequency': '-999'}
        logic = ContributeFlowWriteLogic(dataset_dict)

        logic.process_expected_update_frequency()

        assert logic.dataset_dict['data_update_frequency'] is None

    def test_process_expected_update_frequency_valid(self):
        """Test process_expected_update_frequency with valid value"""
        dataset_dict = {'data_update_frequency': '7'}
        logic = ContributeFlowWriteLogic(dataset_dict)

        logic.process_expected_update_frequency()

        assert logic.dataset_dict['data_update_frequency'] == '7'

    def test_process_methodology_default(self):
        """Test process_methodology with default value"""
        dataset_dict = {'methodology': '-1'}
        logic = ContributeFlowWriteLogic(dataset_dict)

        logic.process_methodology()

        assert logic.dataset_dict['methodology'] is None

    def test_process_methodology_valid(self):
        """Test process_methodology with valid value"""
        dataset_dict = {'methodology': 'Survey'}
        logic = ContributeFlowWriteLogic(dataset_dict)

        logic.process_methodology()

        assert logic.dataset_dict['methodology'] == 'Survey'

    def test_process_methodology_missing(self):
        """Test process_methodology when methodology is not present"""
        dataset_dict = {'name': 'test'}
        logic = ContributeFlowWriteLogic(dataset_dict)

        logic.process_methodology()

        assert 'methodology' not in logic.dataset_dict

    @patch('ckanext.hdx_package.controller_logic.contribute_flow_write_logic._get_action')
    def test_process_maintainer_success(self, mock_get_action, mock_context):
        """Test process_maintainer with successful user lookup"""
        mock_user_show = Mock(return_value={'id': 'user123', 'email': 'test@example.com'})
        mock_get_action.return_value = mock_user_show

        dataset_dict = {'maintainer': 'test_user'}
        logic = ContributeFlowWriteLogic(dataset_dict)

        logic.process_maintainer(mock_context)

        assert logic.dataset_dict['maintainer'] == 'user123'
        assert logic.dataset_dict['maintainer_email'] == 'test@example.com'
        mock_user_show.assert_called_once_with(mock_context, {'id': 'test_user'})

    @patch('ckanext.hdx_package.controller_logic.contribute_flow_write_logic._get_action')
    def test_process_maintainer_not_found(self, mock_get_action, mock_context):
        """Test process_maintainer when user is not found"""
        from ckan.plugins.toolkit import ObjectNotFound

        mock_user_show = Mock(side_effect=ObjectNotFound)
        mock_get_action.return_value = mock_user_show

        dataset_dict = {'maintainer': 'nonexistent_user'}
        logic = ContributeFlowWriteLogic(dataset_dict)

        logic.process_maintainer(mock_context)

        # Should not raise exception, just log
        assert dataset_dict['maintainer'] == 'nonexistent_user'

    @patch('ckanext.hdx_package.controller_logic.contribute_flow_write_logic._get_action')
    def test_process_maintainer_missing(self, mock_get_action, mock_context):
        """Test process_maintainer when maintainer is not in dict"""
        dataset_dict = {'name': 'test'}
        logic = ContributeFlowWriteLogic(dataset_dict)

        logic.process_maintainer(mock_context)

        mock_get_action.assert_not_called()

    def test_process_dataset_preview_save_first_resource(self):
        """Test process_dataset_preview_save with first resource preview"""
        dataset_dict = {'dataset_preview_check': '1', 'dataset_preview_value': vd._DATASET_PREVIEW_FIRST_RESOURCE}
        logic = ContributeFlowWriteLogic(dataset_dict)

        logic.process_dataset_preview_save()

        assert logic.dataset_dict['dataset_preview'] == vd._DATASET_PREVIEW_FIRST_RESOURCE

    def test_process_dataset_preview_save_resource_id(self):
        """Test process_dataset_preview_save with resource ID preview"""
        dataset_dict = {'dataset_preview_check': '1', 'dataset_preview_value': 'resource-123'}
        logic = ContributeFlowWriteLogic(dataset_dict)

        logic.process_dataset_preview_save()

        assert logic.dataset_dict['dataset_preview'] == vd._DATASET_PREVIEW_RESOURCE_ID

    def test_process_dataset_preview_save_no_preview(self):
        """Test process_dataset_preview_save with no preview"""
        dataset_dict = {'dataset_preview_check': '0'}
        logic = ContributeFlowWriteLogic(dataset_dict)

        logic.process_dataset_preview_save()

        assert logic.dataset_dict['dataset_preview'] == vd._DATASET_PREVIEW_NO_PREVIEW

    def test_process_dataset_preview_save_missing_check(self):
        """Test process_dataset_preview_save when check is missing"""
        dataset_dict = {'name': 'test'}
        logic = ContributeFlowWriteLogic(dataset_dict)

        logic.process_dataset_preview_save()

        assert logic.dataset_dict['dataset_preview'] == vd._DATASET_PREVIEW_NO_PREVIEW

    def test_process_resource_grouping_save_with_grouping(self):
        """Test process_resource_grouping_save with grouping string"""
        dataset_dict = {'resource_grouping': 'group1, group2, group3'}
        logic = ContributeFlowWriteLogic(dataset_dict)

        logic.process_resource_grouping_save()

        assert logic.dataset_dict['resource_grouping'] == ['group1', 'group2', 'group3']

    def test_process_resource_grouping_save_empty(self):
        """Test process_resource_grouping_save with no grouping"""
        dataset_dict = {'name': 'test'}
        logic = ContributeFlowWriteLogic(dataset_dict)

        logic.process_resource_grouping_save()

        assert 'resource_grouping' not in logic.dataset_dict

    def test_process_private_and_req_data_missing(self):
        """Test process_private_and_req_data when private is missing"""
        dataset_dict = {'name': 'test'}
        logic = ContributeFlowWriteLogic(dataset_dict)

        logic.process_private_and_req_data()

        assert logic.dataset_dict['private'] == 'True'

    def test_process_private_and_req_data_public(self):
        """Test process_private_and_req_data with public value"""
        dataset_dict = {'private': 'public'}
        logic = ContributeFlowWriteLogic(dataset_dict)

        logic.process_private_and_req_data()

        assert logic.dataset_dict['private'] == 'False'
        assert 'is_requestdata_type' not in logic.dataset_dict

    def test_process_private_and_req_data_private(self):
        """Test process_private_and_req_data with private value"""
        dataset_dict = {'private': 'private'}
        logic = ContributeFlowWriteLogic(dataset_dict)

        logic.process_private_and_req_data()

        assert logic.dataset_dict['private'] == 'True'
        assert 'is_requestdata_type' not in logic.dataset_dict

    def test_process_private_and_req_data_requestdata(self):
        """Test process_private_and_req_data with requestdata value"""
        dataset_dict = {'private': 'requestdata'}
        logic = ContributeFlowWriteLogic(dataset_dict)

        logic.process_private_and_req_data()

        assert logic.dataset_dict['private'] == 'False'
        assert logic.dataset_dict['is_requestdata_type'] == 'True'

    @patch.object(ContributeFlowWriteLogic, 'process_tag_string')
    @patch.object(ContributeFlowWriteLogic, 'process_locations')
    @patch.object(ContributeFlowWriteLogic, 'process_dataset_date')
    @patch.object(ContributeFlowWriteLogic, 'process_expected_update_frequency')
    @patch.object(ContributeFlowWriteLogic, 'process_methodology')
    @patch.object(ContributeFlowWriteLogic, 'process_maintainer')
    @patch.object(ContributeFlowWriteLogic, 'process_dataset_preview_save')
    @patch.object(ContributeFlowWriteLogic, 'process_resource_grouping_save')
    @patch.object(ContributeFlowWriteLogic, 'process_private_and_req_data')
    def test_process_all_calls_all_methods(
        self,
        mock_private,
        mock_grouping,
        mock_preview,
        mock_maintainer,
        mock_methodology,
        mock_frequency,
        mock_date,
        mock_locations,
        mock_tags,
        sample_dataset_dict,
        mock_context,
    ):
        """Test process_all calls all processing methods"""
        logic = ContributeFlowWriteLogic(sample_dataset_dict)

        logic.process_all('test_user')

        mock_tags.assert_called_once()
        mock_locations.assert_called_once()
        mock_date.assert_called_once()
        mock_frequency.assert_called_once()
        mock_methodology.assert_called_once()
        mock_maintainer.assert_called_once()
        mock_preview.assert_called_once()
        mock_grouping.assert_called_once()
        mock_private.assert_called_once()
