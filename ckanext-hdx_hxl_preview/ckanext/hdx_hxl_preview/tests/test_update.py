"""Test module for hdx_hxl_preview actions/update.py"""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
import requests


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


class TestPackageHxlUpdate:
    """Test suite for package_hxl_update function."""

    @patch('ckanext.hdx_hxl_preview.actions.update.model.Vocabulary.get')
    @patch('ckanext.hdx_hxl_preview.actions.update._check_has_hxl_tags')
    @patch('ckanext.hdx_hxl_preview.actions.update._get_action')
    def test_package_hxl_update_creates_view_for_hxl_resource(
        self,
        mock_get_action: Mock,
        mock_check_hxl: Mock,
        mock_vocab_get: Mock
    ) -> None:
        """Test creating HXL preview view for resource with HXL tags."""
        from ckanext.hdx_hxl_preview.actions.update import package_hxl_update

        # Setup mocks
        mock_vocab = Mock()
        mock_vocab.id = 'vocab-123'
        mock_vocab_get.return_value = mock_vocab

        mock_package_show = Mock()
        mock_package_show.return_value = {
            'id': 'pkg-123',
            'private': False,
            'tags': [],
            'resources': [
                {
                    'id': 'res-456',
                    'format': 'csv',
                    'url': 'https://example.com/data.csv'
                }
            ]
        }

        mock_resource_view_list = Mock()
        mock_resource_view_list.return_value = []

        mock_resource_view_create = Mock()
        mock_resource_view_create.return_value = {
            'id': 'view-789',
            'resource_id': 'res-456',
            'view_type': 'hdx_hxl_preview'
        }

        mock_package_patch = Mock()

        def get_action_side_effect(action_name):
            actions = {
                'package_show': mock_package_show,
                'resource_view_list': mock_resource_view_list,
                'resource_view_create': mock_resource_view_create,
                'package_patch': mock_package_patch
            }
            return actions.get(action_name, Mock())

        mock_get_action.side_effect = get_action_side_effect
        mock_check_hxl.return_value = True

        # Execute
        context = {'user': 'test_user'}
        data_dict = {'id': 'pkg-123'}
        result = package_hxl_update(context, data_dict)

        # Assertions
        assert len(result) == 1
        assert result[0]['id'] == 'view-789'
        mock_resource_view_create.assert_called_once()
        created_view = mock_resource_view_create.call_args[0][1]
        assert created_view['resource_id'] == 'res-456'
        assert created_view['title'] == 'Quick Charts'
        assert created_view['view_type'] == 'hdx_hxl_preview'
        mock_package_patch.assert_called_once()

    @patch('ckanext.hdx_hxl_preview.actions.update.model.Vocabulary.get')
    @patch('ckanext.hdx_hxl_preview.actions.update._check_has_hxl_tags')
    @patch('ckanext.hdx_hxl_preview.actions.update._get_action')
    def test_package_hxl_update_skips_private_package(
        self,
        mock_get_action: Mock,
        mock_check_hxl: Mock,
        mock_vocab_get: Mock
    ) -> None:
        """Test that private packages are skipped."""
        from ckanext.hdx_hxl_preview.actions.update import package_hxl_update

        # Setup mocks
        mock_package_show = Mock()
        mock_package_show.return_value = {
            'id': 'pkg-123',
            'private': True,
            'resources': []
        }

        mock_get_action.return_value = mock_package_show

        # Execute
        context = {'user': 'test_user'}
        data_dict = {'id': 'pkg-123'}
        result = package_hxl_update(context, data_dict)

        # Assertions
        assert result == []
        mock_check_hxl.assert_not_called()

    @patch('ckanext.hdx_hxl_preview.actions.update.model.Vocabulary.get')
    @patch('ckanext.hdx_hxl_preview.actions.update._check_has_hxl_tags')
    @patch('ckanext.hdx_hxl_preview.actions.update._get_action')
    def test_package_hxl_update_deletes_view_for_non_hxl_resource(
        self,
        mock_get_action: Mock,
        mock_check_hxl: Mock,
        mock_vocab_get: Mock
    ) -> None:
        """Test deleting HXL preview view when resource no longer has HXL tags."""
        from ckanext.hdx_hxl_preview.actions.update import package_hxl_update

        # Setup mocks
        mock_vocab_get.return_value = None

        mock_package_show = Mock()
        mock_package_show.return_value = {
            'id': 'pkg-123',
            'private': False,
            'tags': [],
            'resources': [
                {
                    'id': 'res-456',
                    'format': 'csv',
                    'url': 'https://example.com/data.csv'
                }
            ]
        }

        mock_resource_view_list = Mock()
        mock_resource_view_list.return_value = [
            {'id': 'view-789', 'view_type': 'hdx_hxl_preview'}
        ]

        mock_resource_view_delete = Mock()

        def get_action_side_effect(action_name):
            actions = {
                'package_show': mock_package_show,
                'resource_view_list': mock_resource_view_list,
                'resource_view_delete': mock_resource_view_delete
            }
            return actions.get(action_name, Mock())

        mock_get_action.side_effect = get_action_side_effect
        mock_check_hxl.return_value = False

        # Execute
        context = {'user': 'test_user'}
        data_dict = {'id': 'pkg-123'}
        result = package_hxl_update(context, data_dict)

        # Assertions
        assert result == []
        mock_resource_view_delete.assert_called_once_with(
            context, {'id': 'view-789'}
        )

    @patch('ckanext.hdx_hxl_preview.actions.update.model.Vocabulary.get')
    @patch('ckanext.hdx_hxl_preview.actions.update._check_has_hxl_tags')
    @patch('ckanext.hdx_hxl_preview.actions.update._get_action')
    def test_package_hxl_update_skips_non_tabular_format(
        self,
        mock_get_action: Mock,
        mock_check_hxl: Mock,
        mock_vocab_get: Mock
    ) -> None:
        """Test that non-tabular formats are skipped."""
        from ckanext.hdx_hxl_preview.actions.update import package_hxl_update

        # Setup mocks
        mock_vocab_get.return_value = None

        mock_package_show = Mock()
        mock_package_show.return_value = {
            'id': 'pkg-123',
            'private': False,
            'tags': [],
            'resources': [
                {
                    'id': 'res-456',
                    'format': 'pdf',
                    'url': 'https://example.com/data.pdf'
                }
            ]
        }

        mock_resource_view_list = Mock()
        mock_resource_view_list.return_value = []

        def get_action_side_effect(action_name):
            actions = {
                'package_show': mock_package_show,
                'resource_view_list': mock_resource_view_list
            }
            return actions.get(action_name, Mock())

        mock_get_action.side_effect = get_action_side_effect

        # Execute
        context = {'user': 'test_user'}
        data_dict = {'id': 'pkg-123'}
        result = package_hxl_update(context, data_dict)

        # Assertions
        assert result == []
        mock_check_hxl.assert_not_called()

    @patch('ckanext.hdx_hxl_preview.actions.update.model.Vocabulary.get')
    @patch('ckanext.hdx_hxl_preview.actions.update._check_has_hxl_tags')
    @patch('ckanext.hdx_hxl_preview.actions.update._get_action')
    def test_package_hxl_update_handles_existing_view(
        self,
        mock_get_action: Mock,
        mock_check_hxl: Mock,
        mock_vocab_get: Mock
    ) -> None:
        """Test that existing HXL views are not duplicated."""
        from ckanext.hdx_hxl_preview.actions.update import package_hxl_update

        # Setup mocks
        mock_vocab_get.return_value = None

        mock_package_show = Mock()
        mock_package_show.return_value = {
            'id': 'pkg-123',
            'private': False,
            'tags': [],
            'resources': [
                {
                    'id': 'res-456',
                    'format': 'csv',
                    'url': 'https://example.com/data.csv'
                }
            ]
        }

        mock_resource_view_list = Mock()
        mock_resource_view_list.return_value = [
            {'id': 'view-789', 'view_type': 'hdx_hxl_preview'}
        ]

        mock_resource_view_create = Mock()

        def get_action_side_effect(action_name):
            actions = {
                'package_show': mock_package_show,
                'resource_view_list': mock_resource_view_list,
                'resource_view_create': mock_resource_view_create
            }
            return actions.get(action_name, Mock())

        mock_get_action.side_effect = get_action_side_effect
        mock_check_hxl.return_value = True

        # Execute
        context = {'user': 'test_user'}
        data_dict = {'id': 'pkg-123'}
        result = package_hxl_update(context, data_dict)

        # Assertions
        assert result == []
        mock_resource_view_create.assert_not_called()

    @patch('ckanext.hdx_hxl_preview.actions.update.model.Vocabulary.get')
    @patch('ckanext.hdx_hxl_preview.actions.update._check_has_hxl_tags')
    @patch('ckanext.hdx_hxl_preview.actions.update._get_action')
    def test_package_hxl_update_adds_hxl_tag(
        self,
        mock_get_action: Mock,
        mock_check_hxl: Mock,
        mock_vocab_get: Mock
    ) -> None:
        """Test that HXL tag is added to package when views are created."""
        from ckanext.hdx_hxl_preview.actions.update import package_hxl_update

        # Setup mocks
        mock_vocab = Mock()
        mock_vocab.id = 'vocab-123'
        mock_vocab_get.return_value = mock_vocab

        mock_package_show = Mock()
        mock_package_show.return_value = {
            'id': 'pkg-123',
            'private': False,
            'tags': [{'name': 'other-tag'}],
            'resources': [
                {
                    'id': 'res-456',
                    'format': 'xlsx',
                    'url': 'https://example.com/data.xlsx'
                }
            ]
        }

        mock_resource_view_list = Mock()
        mock_resource_view_list.return_value = []

        mock_resource_view_create = Mock()
        mock_resource_view_create.return_value = {'id': 'view-789'}

        mock_package_patch = Mock()

        def get_action_side_effect(action_name):
            actions = {
                'package_show': mock_package_show,
                'resource_view_list': mock_resource_view_list,
                'resource_view_create': mock_resource_view_create,
                'package_patch': mock_package_patch
            }
            return actions.get(action_name, Mock())

        mock_get_action.side_effect = get_action_side_effect
        mock_check_hxl.return_value = True

        # Execute
        context = {'user': 'test_user'}
        data_dict = {'id': 'pkg-123'}
        result = package_hxl_update(context, data_dict)

        # Assertions
        assert len(result) == 1
        mock_package_patch.assert_called_once()
        patch_call = mock_package_patch.call_args[0][1]
        assert len(patch_call['tags']) == 2
        assert any(tag['name'] == 'hxl' for tag in patch_call['tags'])
        assert any(tag['name'] == 'other-tag' for tag in patch_call['tags'])
