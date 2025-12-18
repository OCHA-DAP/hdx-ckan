import pytest
from unittest.mock import patch
from ckanext.hdx_package.controller_logic.dataset_view_logic import process_shapes, has_shape_info


class TestDatasetViewLogic:
    """Tests for dataset view logic"""

    @pytest.fixture
    def mock_get_latest_shape_info(self):
        """Mock get_latest_shape_info"""
        with patch('ckanext.hdx_package.controller_logic.dataset_view_logic.get_latest_shape_info') as mock_func:
            mock_func.reset_mock()  # Ensure clean state for each test
            yield mock_func

    @pytest.fixture
    def mock_config(self):
        """Mock CKAN config"""
        with patch('ckanext.hdx_package.controller_logic.dataset_view_logic.config') as mock_cfg:
            mock_cfg.get.return_value = 'https://gis.example.com/tiles/{resource_id}'
            yield mock_cfg

    @pytest.fixture
    def sample_shape_info(self):
        """Sample shape info data"""
        return {
            'layer_id': 'layer-123',
            'state': 'success',
            'bounding_box': [1.0, 2.0, 3.0, 4.0],
            'layer_fields': ['field1', 'field2'],
        }

    @pytest.fixture
    def basic_resource(self):
        """Basic resource without shape info"""
        return {
            'id': 'res-1',
            'name': 'Test Resource',
            'format': 'CSV',
        }

    @pytest.fixture
    def gis_resource(self, sample_shape_info):
        """GIS resource with shape info"""
        return {'id': 'res-gis-1', 'name': 'Shapefile Data', 'format': 'SHP', 'shape_info': sample_shape_info}

    def test_process_shapes_empty_resources(self, mock_config):
        """Test process_shapes with empty resources list"""
        result = process_shapes([])

        assert result == []

    def test_process_shapes_no_shape_resources(self, mock_config, basic_resource):
        """Test process_shapes with resources without shape info"""
        result = process_shapes([basic_resource])

        assert result == []

    def test_process_shapes_single_gis_resource(
        self, mock_config, mock_get_latest_shape_info, gis_resource, sample_shape_info
    ):
        """Test process_shapes with single GIS resource"""
        mock_get_latest_shape_info.return_value = sample_shape_info

        result = process_shapes([gis_resource])

        assert len(result) == 1
        assert result[0]['resource_name'] == 'Shapefile Data'
        assert result[0]['resource_format'] == 'SHP'
        assert result[0]['url'] == 'https://gis.example.com/tiles/layer-123'
        assert result[0]['bounding_box'] == [1.0, 2.0, 3.0, 4.0]
        assert result[0]['layer_fields'] == ['field1', 'field2']
        assert result[0]['layer_id'] == 'layer-123'

    def test_process_shapes_multiple_resources_mixed(
        self, mock_config, mock_get_latest_shape_info, basic_resource, gis_resource, sample_shape_info
    ):
        """Test process_shapes with mixed resource types"""
        mock_get_latest_shape_info.return_value = sample_shape_info

        resources = [basic_resource, gis_resource]
        result = process_shapes(resources)

        assert len(result) == 1
        assert result[0]['resource_name'] == 'Shapefile Data'

    def test_process_shapes_with_target_id_first(self, mock_config, mock_get_latest_shape_info, sample_shape_info):
        """Test process_shapes prioritizes resource with matching id"""
        mock_get_latest_shape_info.return_value = sample_shape_info

        resources = [
            {'id': 'res-1', 'name': 'First Shape', 'format': 'SHP', 'shape_info': sample_shape_info},
            {'id': 'res-2', 'name': 'Second Shape', 'format': 'GEOJSON', 'shape_info': sample_shape_info},
        ]

        result = process_shapes(resources, id='res-2')

        assert len(result) == 2
        assert result[0]['resource_name'] == 'Second Shape'
        assert result[1]['resource_name'] == 'First Shape'

    def test_process_shapes_with_target_id_reordering(self, mock_config, mock_get_latest_shape_info, sample_shape_info):
        """Test process_shapes moves matching id to front"""
        shape_info_1 = {**sample_shape_info, 'layer_id': 'layer-1'}
        shape_info_2 = {**sample_shape_info, 'layer_id': 'layer-2'}
        shape_info_3 = {**sample_shape_info, 'layer_id': 'layer-3'}

        shape_info_map = {'res-1': shape_info_1, 'res-2': shape_info_2, 'res-3': shape_info_3}

        mock_get_latest_shape_info.side_effect = lambda resource: shape_info_map[resource['id']]

        resources = [
            {'id': 'res-1', 'name': 'First', 'format': 'SHP', 'shape_info': shape_info_1},
            {'id': 'res-2', 'name': 'Second', 'format': 'SHP', 'shape_info': shape_info_2},
            {'id': 'res-3', 'name': 'Third', 'format': 'SHP', 'shape_info': shape_info_3},
        ]

        result = process_shapes(resources, id='res-2')

        assert len(result) == 3
        assert result[0]['resource_name'] == 'Second'
        assert result[0]['layer_id'] == 'layer-2'
        assert result[1]['resource_name'] == 'First'
        assert result[1]['layer_id'] == 'layer-1'
        assert result[2]['resource_name'] == 'Third'
        assert result[2]['layer_id'] == 'layer-3'

    def test_process_shapes_multiple_gis_formats(self, mock_config, mock_get_latest_shape_info, sample_shape_info):
        """Test process_shapes with different GIS formats"""
        mock_get_latest_shape_info.return_value = sample_shape_info

        resources = [
            {'id': 'r1', 'name': 'Shape', 'format': 'SHP', 'shape_info': sample_shape_info},
            {'id': 'r2', 'name': 'GeoJSON', 'format': 'GEOJSON', 'shape_info': sample_shape_info},
            {'id': 'r3', 'name': 'KML', 'format': 'KML', 'shape_info': sample_shape_info},
        ]

        result = process_shapes(resources)

        assert len(result) == 3
        assert result[0]['resource_format'] == 'SHP'
        assert result[1]['resource_format'] == 'GEOJSON'
        assert result[2]['resource_format'] == 'KML'

    def test_process_shapes_without_layer_fields(self, mock_config, mock_get_latest_shape_info, sample_shape_info):
        """Test process_shapes when layer_fields is missing"""
        shape_info_no_fields = {**sample_shape_info}
        del shape_info_no_fields['layer_fields']

        mock_get_latest_shape_info.return_value = shape_info_no_fields

        resource = {'id': 'res-1', 'name': 'Shape', 'format': 'SHP', 'shape_info': shape_info_no_fields}

        result = process_shapes([resource])

        assert len(result) == 1
        assert result[0]['layer_fields'] == []

    def test_process_shapes_url_replacement(self, mock_config, mock_get_latest_shape_info, sample_shape_info):
        """Test process_shapes correctly replaces resource_id in URL"""
        mock_config.get.return_value = 'https://tiles.example.com/{resource_id}/tiles'
        mock_get_latest_shape_info.return_value = {**sample_shape_info, 'layer_id': 'abc-123'}

        resource = {'id': 'res-1', 'name': 'Shape', 'format': 'SHP', 'shape_info': sample_shape_info}

        result = process_shapes([resource])

        assert result[0]['url'] == 'https://tiles.example.com/abc-123/tiles'

    def test_has_shape_info_with_successful_shape(self, mock_get_latest_shape_info, sample_shape_info):
        """Test has_shape_info with successful shape processing"""
        mock_get_latest_shape_info.return_value = sample_shape_info

        resource = {'format': 'SHP', 'shape_info': sample_shape_info}

        result = has_shape_info(resource)

        assert result is not None
        assert result['type'] == 'hdx_geo_preview'
        assert result['default'] is None

    def test_has_shape_info_not_gis_format(self, mock_get_latest_shape_info):
        """Test has_shape_info with non-GIS format"""
        resource = {'format': 'CSV', 'shape_info': {}}

        result = has_shape_info(resource)

        assert result is None
        mock_get_latest_shape_info.assert_not_called()

    def test_has_shape_info_no_shape_info(self, mock_get_latest_shape_info):
        """Test has_shape_info when shape_info is missing"""
        resource = {'format': 'SHP'}

        result = has_shape_info(resource)

        assert result is None
        mock_get_latest_shape_info.assert_not_called()

    def test_has_shape_info_empty_shape_info(self, mock_get_latest_shape_info):
        """Test has_shape_info with empty shape_info"""
        resource = {'format': 'SHP', 'shape_info': None}

        result = has_shape_info(resource)

        assert result is None
        mock_get_latest_shape_info.assert_not_called()

    def test_has_shape_info_failed_state(self, mock_get_latest_shape_info):
        """Test has_shape_info with failed processing state"""
        mock_get_latest_shape_info.return_value = {'layer_id': 'layer-123', 'state': 'failed'}

        resource = {'format': 'SHP', 'shape_info': {'state': 'failed'}}

        result = has_shape_info(resource)

        assert result is None

    def test_has_shape_info_processing_state(self, mock_get_latest_shape_info):
        """Test has_shape_info with processing state"""
        mock_get_latest_shape_info.return_value = {'layer_id': 'layer-123', 'state': 'processing'}

        resource = {'format': 'SHP', 'shape_info': {'state': 'processing'}}

        result = has_shape_info(resource)

        assert result is None

    def test_has_shape_info_missing_state(self, mock_get_latest_shape_info):
        """Test has_shape_info with missing state"""
        mock_get_latest_shape_info.return_value = {'layer_id': 'layer-123'}

        resource = {'format': 'SHP', 'shape_info': {}}

        result = has_shape_info(resource)

        assert result is None

    def test_has_shape_info_case_insensitive_format(self, mock_get_latest_shape_info, sample_shape_info):
        """Test has_shape_info with different case formats"""
        mock_get_latest_shape_info.return_value = sample_shape_info

        formats = ['shp', 'SHP', 'Shp', 'geojson', 'GEOJSON', 'GeoJSON']

        for fmt in formats:
            resource = {'format': fmt, 'shape_info': sample_shape_info}

            result = has_shape_info(resource)
            assert result is not None

    def test_has_shape_info_empty_format(self, mock_get_latest_shape_info):
        """Test has_shape_info with empty format"""
        resource = {'format': '', 'shape_info': {}}

        result = has_shape_info(resource)

        assert result is None

    def test_has_shape_info_missing_format(self, mock_get_latest_shape_info):
        """Test has_shape_info with missing format field"""
        resource = {'shape_info': {}}

        result = has_shape_info(resource)

        assert result is None

    def test_process_shapes_preserves_all_shape_info_fields(self, mock_config, mock_get_latest_shape_info):
        """Test process_shapes includes all fields from shape_info"""
        shape_info = {
            'layer_id': 'layer-xyz',
            'state': 'success',
            'bounding_box': [-10.5, 20.3, 30.7, 40.9],
            'layer_fields': ['name', 'population', 'area'],
        }

        mock_get_latest_shape_info.return_value = shape_info

        resource = {'id': 'res-1', 'name': 'Detailed Shape', 'format': 'SHP', 'shape_info': shape_info}

        result = process_shapes([resource])

        assert len(result) == 1
        assert result[0]['bounding_box'] == [-10.5, 20.3, 30.7, 40.9]
        assert result[0]['layer_fields'] == ['name', 'population', 'area']
        assert result[0]['layer_id'] == 'layer-xyz'

    def test_process_shapes_calls_get_latest_shape_info(self, mock_config, sample_shape_info):
        """Test process_shapes calls get_latest_shape_info for GIS resources"""
        import ckanext.hdx_package.controller_logic.dataset_view_logic as dvl_module

        # Create a fresh mock for this test only
        with patch.object(dvl_module, 'get_latest_shape_info') as mock_func:
            mock_func.return_value = sample_shape_info

            resources = [
                {'id': 'r1', 'name': 'S1', 'format': 'SHP', 'shape_info': sample_shape_info},
                {'id': 'r2', 'name': 'S2', 'format': 'SHP', 'shape_info': sample_shape_info},
            ]

            result = process_shapes(resources)

            # Verify the function was called (implementation may call multiple times per resource)
            assert mock_func.call_count >= 2
            assert len(result) == 2

            # Verify each resource was processed with correct data
            assert result[0]['resource_name'] == 'S1'
            assert result[0]['layer_id'] == 'layer-123'
            assert result[1]['resource_name'] == 'S2'
            assert result[1]['layer_id'] == 'layer-123'

    def test_process_shapes_calls_get_latest_shape_info_2(self, mock_config, sample_shape_info):
        """Test process_shapes calls get_latest_shape_info for each resource"""
        import ckanext.hdx_package.controller_logic.dataset_view_logic as dvl_module

        # Create a fresh mock for this test only
        with patch.object(dvl_module, 'get_latest_shape_info') as mock_func:
            mock_func.return_value = sample_shape_info

            resources = [
                {'id': 'r1', 'name': 'S1', 'format': 'SHP', 'shape_info': sample_shape_info},
                {'id': 'r2', 'name': 'S2', 'format': 'SHP', 'shape_info': sample_shape_info},
            ]

            result = process_shapes(resources)

            # The function calls get_latest_shape_info twice per resource:
            # once for filtering and once for processing
            assert mock_func.call_count == 4
            assert len(result) == 2

            # Verify the calls were made with correct resources
            called_ids = [call[0][0]['id'] for call in mock_func.call_args_list]
            assert called_ids.count('r1') == 2
            assert called_ids.count('r2') == 2

    def test_has_shape_info_calls_get_latest_shape_info_once(self, mock_get_latest_shape_info, sample_shape_info):
        """Test has_shape_info calls get_latest_shape_info only once"""
        mock_get_latest_shape_info.return_value = sample_shape_info

        resource = {'format': 'SHP', 'shape_info': sample_shape_info}

        has_shape_info(resource)

        mock_get_latest_shape_info.assert_called_once_with(resource)

    def test_process_shapes_none_id_parameter(self, mock_config, mock_get_latest_shape_info, sample_shape_info):
        """Test process_shapes with explicit None id parameter"""
        mock_get_latest_shape_info.return_value = sample_shape_info

        resources = [
            {'id': 'r1', 'name': 'S1', 'format': 'SHP', 'shape_info': sample_shape_info},
            {'id': 'r2', 'name': 'S2', 'format': 'SHP', 'shape_info': sample_shape_info},
        ]

        result = process_shapes(resources, id=None)

        assert len(result) == 2
        assert result[0]['resource_name'] == 'S1'
        assert result[1]['resource_name'] == 'S2'

    def test_process_shapes_nonexistent_id(self, mock_config, mock_get_latest_shape_info, sample_shape_info):
        """Test process_shapes with id that doesn't match any resource"""
        mock_get_latest_shape_info.return_value = sample_shape_info

        resources = [
            {'id': 'r1', 'name': 'S1', 'format': 'SHP', 'shape_info': sample_shape_info},
            {'id': 'r2', 'name': 'S2', 'format': 'SHP', 'shape_info': sample_shape_info},
        ]

        result = process_shapes(resources, id='nonexistent')

        assert len(result) == 2
        # Order should be unchanged since no match
        assert result[0]['resource_name'] == 'S1'
        assert result[1]['resource_name'] == 'S2'
