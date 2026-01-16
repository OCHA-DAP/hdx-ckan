"""Test module for hdx_hxl_preview actions/update.py"""

import pytest
from unittest.mock import Mock, patch


class TestCheckHasHxlTags:
    """Test suite for _check_has_hxl_tags function."""

    @patch('ckanext.hdx_hxl_preview.actions.update.requests.get')
    @patch('ckanext.hdx_hxl_preview.actions.update.config')
    def test_check_has_hxl_tags_success(
        self,
        mock_config: Mock,
        mock_requests_get: Mock
    ) -> None:
        """Test HXL tag detection when tags are present."""
        from ckanext.hdx_hxl_preview.actions.update import _check_has_hxl_tags

        # Setup mocks
        mock_config.get.return_value = 'https://proxy.hxlstandard.org'
        mock_response = Mock()
        mock_response.json.return_value = {'status': True}
        mock_requests_get.return_value = mock_response

        # Execute
        result = _check_has_hxl_tags('https://example.com/data.csv')

        # Assertions
        assert result is True
        mock_requests_get.assert_called_once()
        mock_response.raise_for_status.assert_called_once()
        mock_response.close.assert_called_once()

    @patch('ckanext.hdx_hxl_preview.actions.update.requests.get')
    @patch('ckanext.hdx_hxl_preview.actions.update.config')
    def test_check_has_hxl_tags_no_tags(
        self,
        mock_config: Mock,
        mock_requests_get: Mock
    ) -> None:
        """Test HXL tag detection when tags are not present."""
        from ckanext.hdx_hxl_preview.actions.update import _check_has_hxl_tags

        # Setup mocks
        mock_config.get.return_value = 'https://proxy.hxlstandard.org'
        mock_response = Mock()
        mock_response.json.return_value = {'status': False}
        mock_requests_get.return_value = mock_response

        # Execute
        result = _check_has_hxl_tags('https://example.com/data.csv')

        # Assertions
        assert result is False
        mock_response.close.assert_called_once()

    @patch('ckanext.hdx_hxl_preview.actions.update.requests.get')
    @patch('ckanext.hdx_hxl_preview.actions.update.config')
    def test_check_has_hxl_tags_empty_response(
        self,
        mock_config: Mock,
        mock_requests_get: Mock
    ) -> None:
        """Test HXL tag detection with empty response."""
        from ckanext.hdx_hxl_preview.actions.update import _check_has_hxl_tags

        # Setup mocks
        mock_config.get.return_value = 'https://proxy.hxlstandard.org'
        mock_response = Mock()
        mock_response.json.return_value = {}
        mock_requests_get.return_value = mock_response

        # Execute
        result = _check_has_hxl_tags('https://example.com/data.csv')

        # Assertions
        assert result is False

    @patch('ckanext.hdx_hxl_preview.actions.update.requests.get')
    @patch('ckanext.hdx_hxl_preview.actions.update.config')
    def test_check_has_hxl_tags_with_path_in_proxy_url(
        self,
        mock_config: Mock,
        mock_requests_get: Mock
    ) -> None:
        """Test HXL tag detection when proxy URL includes a path."""
        from ckanext.hdx_hxl_preview.actions.update import _check_has_hxl_tags

        # Setup mocks
        mock_config.get.return_value = 'https://proxy.hxlstandard.org/api'
        mock_response = Mock()
        mock_response.json.return_value = {'status': True}
        mock_requests_get.return_value = mock_response

        # Execute
        result = _check_has_hxl_tags('https://example.com/data.csv')

        # Assertions
        assert result is True
        call_args = mock_requests_get.call_args
        assert '/api/hxl-test.json' in call_args[0][0]


class TestViewAlreadyExists:
    """Test suite for _view_already_exists function."""

    def test_view_already_exists_found(self) -> None:
        """Test finding an existing HXL preview view."""
        from ckanext.hdx_hxl_preview.actions.update import _view_already_exists

        view_list = [
            {'id': 'view-1', 'view_type': 'grid'},
            {'id': 'view-2', 'view_type': 'hdx_hxl_preview'},
            {'id': 'view-3', 'view_type': 'chart'}
        ]

        result = _view_already_exists(view_list)

        assert result is not None
        assert result['id'] == 'view-2'
        assert result['view_type'] == 'hdx_hxl_preview'

    def test_view_already_exists_not_found(self) -> None:
        """Test when no HXL preview view exists."""
        from ckanext.hdx_hxl_preview.actions.update import _view_already_exists

        view_list = [
            {'id': 'view-1', 'view_type': 'grid'},
            {'id': 'view-3', 'view_type': 'chart'}
        ]

        result = _view_already_exists(view_list)

        assert result is None

    def test_view_already_exists_empty_list(self) -> None:
        """Test with empty view list."""
        from ckanext.hdx_hxl_preview.actions.update import _view_already_exists

        result = _view_already_exists([])

        assert result is None

    def test_view_already_exists_none_list(self) -> None:
        """Test with None view list."""
        from ckanext.hdx_hxl_preview.actions.update import _view_already_exists

        result = _view_already_exists(None)

        assert result is None
