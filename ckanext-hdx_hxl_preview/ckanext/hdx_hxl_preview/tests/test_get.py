"""Test module for hdx_hxl_preview actions/get.py"""

from unittest.mock import Mock, patch


class TestHxlPreviewIframeUrlShow:
    """Test suite for hxl_preview_iframe_url_show function."""

    @patch('ckanext.hdx_hxl_preview.actions.get.h.render_datetime')
    @patch('ckanext.hdx_hxl_preview.actions.get.h.url_for')
    @patch('ckanext.hdx_hxl_preview.actions.get._get_action')
    @patch('ckanext.hdx_hxl_preview.actions.get.config')
    def test_hxl_preview_iframe_url_show_basic(
        self, mock_config: Mock, mock_get_action: Mock, mock_url_for: Mock, mock_render_datetime: Mock
    ) -> None:
        """Test basic URL generation with minimal data."""
        from ckanext.hdx_hxl_preview.actions.get import hxl_preview_iframe_url_show

        # Setup mocks
        mock_config.get.side_effect = lambda key: {
            'hdx.hxl_preview_app.url': 'https://hxl-preview.example.com',
            'ckan.site_url': 'https://data.example.com',
        }.get(key, '')

        mock_package_show = Mock()
        mock_package_show.return_value = {'id': 'pkg-123', 'dataset_source': 'Example Source'}
        mock_get_action.return_value = mock_package_show

        mock_url_for.side_effect = lambda route, **kwargs: {
            ('dataset.read',): 'https://data.example.com/dataset/pkg-123',
            ('resource.read',): 'https://data.example.com/dataset/pkg-123/resource/res-456',
        }.get((route,), '')

        mock_render_datetime.return_value = '2024-01-15 10:30:00'

        # Test data
        context = {'has_modify_permission': False}
        data_dict = {
            'resource': {
                'id': 'res-456',
                'package_id': 'pkg-123',
                'url': 'https://example.com/data.csv',
                'created': '2024-01-15T10:30:00',
            },
            'resource_view': {'id': 'view-789'},
        }

        # Execute
        result = hxl_preview_iframe_url_show(context, data_dict)

        # Assertions
        assert result.startswith('https://hxl-preview.example.com/show;')
        assert 'url=https' in result
        assert 'resource_view_id=view-789' in result
        assert 'has_modify_permission=false' in result
        assert 'embeddedSource=Example' in result
        mock_package_show.assert_called_once_with(context, {'id': 'pkg-123'})

    @patch('ckanext.hdx_hxl_preview.actions.get.h.render_datetime')
    @patch('ckanext.hdx_hxl_preview.actions.get.h.url_for')
    @patch('ckanext.hdx_hxl_preview.actions.get._get_action')
    @patch('ckanext.hdx_hxl_preview.actions.get.config')
    def test_hxl_preview_iframe_url_show_with_modify_permission(
        self, mock_config: Mock, mock_get_action: Mock, mock_url_for: Mock, mock_render_datetime: Mock
    ) -> None:
        """Test URL generation with modify permission enabled."""
        from ckanext.hdx_hxl_preview.actions.get import hxl_preview_iframe_url_show

        # Setup mocks
        mock_config.get.side_effect = lambda key: {
            'hdx.hxl_preview_app.url': 'https://hxl-preview.example.com',
            'ckan.site_url': 'https://data.example.com',
        }.get(key, '')

        mock_package_show = Mock()
        mock_package_show.return_value = {'id': 'pkg-123', 'dataset_source': 'Test Source'}
        mock_get_action.return_value = mock_package_show

        mock_url_for.side_effect = lambda route, **kwargs: 'https://data.example.com/url'
        mock_render_datetime.return_value = '2024-01-15 10:30:00'

        # Test data
        context = {'has_modify_permission': True}
        data_dict = {
            'resource': {
                'id': 'res-456',
                'package_id': 'pkg-123',
                'url': 'https://example.com/data.csv',
                'last_modified': '2024-01-15T10:30:00',
            },
            'resource_view': {'id': 'view-789'},
        }

        # Execute
        result = hxl_preview_iframe_url_show(context, data_dict)

        # Assertions
        assert 'has_modify_permission=true' in result

    @patch('ckanext.hdx_hxl_preview.actions.get.h.render_datetime')
    @patch('ckanext.hdx_hxl_preview.actions.get.h.url_for')
    @patch('ckanext.hdx_hxl_preview.actions.get._get_action')
    @patch('ckanext.hdx_hxl_preview.actions.get.config')
    def test_hxl_preview_iframe_url_show_with_last_modified(
        self, mock_config: Mock, mock_get_action: Mock, mock_url_for: Mock, mock_render_datetime: Mock
    ) -> None:
        """Test URL generation uses last_modified over created date."""
        from ckanext.hdx_hxl_preview.actions.get import hxl_preview_iframe_url_show

        # Setup mocks
        mock_config.get.side_effect = lambda key: {
            'hdx.hxl_preview_app.url': 'https://hxl-preview.example.com',
            'ckan.site_url': 'https://data.example.com',
        }.get(key, '')

        mock_package_show = Mock()
        mock_package_show.return_value = {'id': 'pkg-123', 'dataset_source': ''}
        mock_get_action.return_value = mock_package_show

        mock_url_for.return_value = 'https://data.example.com/url'
        mock_render_datetime.return_value = 'Modified Date'

        # Test data
        context = {'has_modify_permission': False}
        data_dict = {
            'resource': {
                'id': 'res-456',
                'package_id': 'pkg-123',
                'url': 'https://example.com/data.csv',
                'last_modified': '2024-01-20T10:30:00',
                'created': '2024-01-15T10:30:00',
            },
            'resource_view': {'id': 'view-789'},
        }

        # Execute
        hxl_preview_iframe_url_show(context, data_dict)

        # Assertions - should use last_modified
        mock_render_datetime.assert_called_once_with('2024-01-20T10:30:00')

    @patch('ckanext.hdx_hxl_preview.actions.get.h.render_datetime')
    @patch('ckanext.hdx_hxl_preview.actions.get.h.url_for')
    @patch('ckanext.hdx_hxl_preview.actions.get._get_action')
    @patch('ckanext.hdx_hxl_preview.actions.get.config')
    def test_hxl_preview_iframe_url_show_with_special_characters(
        self, mock_config: Mock, mock_get_action: Mock, mock_url_for: Mock, mock_render_datetime: Mock
    ) -> None:
        """Test URL generation properly encodes special characters."""
        from ckanext.hdx_hxl_preview.actions.get import hxl_preview_iframe_url_show

        # Setup mocks
        mock_config.get.side_effect = lambda key: {
            'hdx.hxl_preview_app.url': 'https://hxl-preview.example.com',
            'ckan.site_url': 'https://data.example.com',
        }.get(key, '')

        mock_package_show = Mock()
        mock_package_show.return_value = {'id': 'pkg-123', 'dataset_source': 'Source & Data © 2024'}
        mock_get_action.return_value = mock_package_show

        mock_url_for.return_value = 'https://data.example.com/url'
        mock_render_datetime.return_value = '2024-01-15 10:30:00'

        # Test data
        context = {'has_modify_permission': False}
        data_dict = {
            'resource': {
                'id': 'res-456',
                'package_id': 'pkg-123',
                'url': 'https://example.com/data.csv',
                'created': '2024-01-15T10:30:00',
            },
            'resource_view': {'id': 'view-789'},
        }

        # Execute
        result = hxl_preview_iframe_url_show(context, data_dict)

        # Assertions - special characters should be URL encoded
        assert 'embeddedSource=' in result
        assert '&' not in result.split('embeddedSource=')[1].split(';')[0] or '%26' in result


from urllib.parse import unquote


class TestPrivateHelperFunctions:
    """Test suite for private helper functions."""

    @patch('ckanext.hdx_hxl_preview.actions.get.h.render_datetime')
    @patch('ckanext.hdx_hxl_preview.actions.get.h.url_for')
    @patch('ckanext.hdx_hxl_preview.actions.get._get_action')
    @patch('ckanext.hdx_hxl_preview.actions.get.config')
    def test_ckan_domain_used_in_url_generation(
        self, mock_config: Mock, mock_get_action: Mock, mock_url_for: Mock, mock_render_datetime: Mock
    ) -> None:
        """Test that CKAN domain is properly extracted and used in URL generation."""
        from ckanext.hdx_hxl_preview.actions.get import hxl_preview_iframe_url_show

        # Setup mocks - test domain extraction
        mock_config.get.side_effect = lambda key: {
            'hdx.hxl_preview_app.url': 'https://hxl-preview.example.com',
            'ckan.site_url': 'https://data.example.com:8080/path',
        }.get(key, '')

        mock_package_show = Mock()
        mock_package_show.return_value = {'id': 'pkg-123', 'dataset_source': ''}
        mock_get_action.return_value = mock_package_show

        mock_url_for.return_value = 'https://data.example.com/url'
        mock_render_datetime.return_value = '2024-01-15 10:30:00'

        context = {'has_modify_permission': False}
        data_dict = {
            'resource': {
                'id': 'res-456',
                'package_id': 'pkg-123',
                'url': 'https://example.com/data.csv',
                'created': '2024-01-15T10:30:00',
            },
            'resource_view': {'id': 'view-789'},
        }

        result = hxl_preview_iframe_url_show(context, data_dict)

        # Verify domain is used without protocol in the result (URL-encoded)
        assert (
            'hdx_domain=%2F%2Fdata.example.com%3A8080%2Fpath' in result
            or 'hdx_domain=%2F%2Fdata.example.com%3A8080' in result
        )

        # Verify the decoded domain matches expected format
        decoded_result = unquote(result)
        assert '//data.example.com:8080' in decoded_result
        assert 'https://data.example.com' not in decoded_result.split('hdx_domain=')[1].split(';')[0]
