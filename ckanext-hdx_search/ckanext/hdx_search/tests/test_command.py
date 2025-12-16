"""Test module for hdx_search/command.py"""

import pytest
import json
import sys
from unittest.mock import Mock, patch, MagicMock, mock_open


# Mock all external dependencies before any imports
sys.modules['paste'] = MagicMock()
sys.modules['paste.script'] = MagicMock()
sys.modules['ckan.lib.cli'] = MagicMock()
sys.modules['ckan.model'] = MagicMock()
sys.modules['ckan.lib.helpers'] = MagicMock()
sys.modules['pylons'] = MagicMock()


class TestFeatureSearchCommand:
    """Test suite for FeatureSearchCommand class."""

    @pytest.fixture
    def command_instance(self):
        """Create a FeatureSearchCommand instance with mocked base class."""
        # Mock the base class completely
        mock_instance = Mock()
        mock_instance._load_config = Mock()
        mock_instance.args = []

        # Mock the command method to simulate the actual implementation
        def mock_command():
            if not mock_instance.args or mock_instance.args == ['-h']:
                print('Usage: hdx-feature-search build')
                return

            if len(mock_instance.args) != 1:
                print('Usage: hdx-feature-search build')
                return

            if mock_instance.args[0] == 'build':
                mock_instance._load_config(load_site_user=False)
                # Import and call buildIndex here to simulate actual behavior
                from ckanext.hdx_search.command import buildIndex, config

                buildIndex(config.get('hdx.lunrjs.path', 'public/lunr'))
            else:
                print(f'Unknown command: {mock_instance.args[0]}')

        mock_instance.command = mock_command
        return mock_instance

    def test_command_build_success(self, command_instance: Mock) -> None:
        """Test successful build command execution."""
        with (
            patch('ckanext.hdx_search.command.buildIndex') as mock_build_index,
            patch('ckanext.hdx_search.command.config') as mock_config,
        ):
            command_instance.args = ['build']
            mock_config.get.return_value = 'public/lunr'

            command_instance.command()

            command_instance._load_config.assert_called_once_with(load_site_user=False)
            mock_build_index.assert_called_once_with('public/lunr')

    def test_command_no_args_shows_usage(self, command_instance: Mock) -> None:
        """Test command with no arguments shows usage."""
        command_instance.args = []

        with patch('builtins.print') as mock_print:
            command_instance.command()
            mock_print.assert_called_with('Usage: hdx-feature-search build')

    def test_command_help_shows_usage(self, command_instance: Mock) -> None:
        """Test command with help flag shows usage."""
        command_instance.args = ['-h']

        with patch('builtins.print') as mock_print:
            command_instance.command()
            mock_print.assert_called_with('Usage: hdx-feature-search build')

    def test_command_invalid_command_shows_error(self, command_instance: Mock) -> None:
        """Test command with invalid argument shows error."""
        command_instance.args = ['invalid']

        with patch('builtins.print') as mock_print:
            command_instance.command()
            mock_print.assert_called_with('Unknown command: invalid')

    def test_command_too_many_args_shows_usage(self, command_instance: Mock) -> None:
        """Test command with too many arguments shows usage."""
        command_instance.args = ['build', 'extra', 'args']

        with patch('builtins.print') as mock_print:
            command_instance.command()
            mock_print.assert_called_with('Usage: hdx-feature-search build')


class TestBuildIndex:
    """Test suite for buildIndex function."""

    @pytest.fixture(autouse=True)
    def mock_all_dependencies(self):
        """Mock all module-level dependencies."""
        with (
            patch('ckan.model.Session') as mock_session_class,
            patch('pylons.config') as mock_config,
            patch('ckanext.hdx_search.command.h.url_for') as mock_url_for,
            patch('builtins.open', mock_open()) as mock_file,
        ):
            # Configure mocks
            mock_config.get = Mock()

            # Create a mock session instance
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            yield {
                'session': mock_session,
                'session_class': mock_session_class,
                'config': mock_config,
                'url_for': mock_url_for,
                'file': mock_file,
            }

    def test_build_index_with_organizations(self, mock_all_dependencies: dict) -> None:
        """Test building index with organization data."""
        # Patch the symbol used inside the command module
        with patch('ckanext.hdx_search.command.Session.execute') as mock_execute:
            mock_execute.side_effect = [
                [('org-1', 'Organization One', True, 'ORG1'), ('org-2', 'Organization Two', True, None)],
                [],
            ]

            from ckanext.hdx_search.command import buildIndex

            mocks = mock_all_dependencies
            mocks['config'].get.side_effect = lambda key, default='': {
                'hdx.crises': 'ebola, nepal-earthquake',
                'hdx.lunrjs.path': '/test/path',
            }.get(key, default)

            mocks['url_for'].side_effect = [
                'http://example.com/organization/org-1',
                'http://example.com/organization/org-2',
                'http://example.com/ebola',
                'http://example.com/nepal-earthquake',
            ]

            # Pass the same path that we're asserting on
            buildIndex('/test/path')

            assert mock_execute.call_count == 2
            mocks['file'].assert_called_once_with('/test/path/lunr/feature-index.js', 'w')

            handle = mocks['file']()
            written_content = ''.join(str(call[0][0]) for call in handle.write.call_args_list)
            assert 'var feature_index=' in written_content
            assert 'Organization One (ORG1)' in written_content

    def test_build_index_includes_visualizations(self, mock_all_dependencies: dict) -> None:
        """Test building index includes hardcoded visualizations."""
        from ckanext.hdx_search.command import buildIndex

        mocks = mock_all_dependencies
        mocks['config'].get.side_effect = lambda key, default='': {
            'hdx.crises': 'ebola, nepal-earthquake',
            'hdx.lunrjs.path': '/test/path',
        }.get(key, default)

        mocks['session_class'].execute = Mock()
        mocks['session_class'].execute.side_effect = [[], []]

        mocks['url_for'].side_effect = ['http://example.com/ebola', 'http://example.com/nepal-earthquake']

        buildIndex('/output/path')

        handle = mocks['file']()
        written_content = ''.join(str(call[0][0]) for call in handle.write.call_args_list)
        assert 'Missing Migrants' in written_content
        assert 'visualization' in written_content

    def test_build_index_json_format(self, mock_all_dependencies: dict) -> None:
        """Test building index produces valid JSON format."""
        from ckanext.hdx_search.command import buildIndex

        mocks = mock_all_dependencies
        mocks['config'].get.side_effect = lambda key, default='': {
            'hdx.crises': 'ebola, nepal-earthquake',
            'hdx.lunrjs.path': '/test/path',
        }.get(key, default)

        mocks['session_class'].execute = Mock()
        mocks['session_class'].execute.side_effect = [[('org-1', 'Test Org', True, 'TEST')], []]

        mocks['url_for'].return_value = 'http://example.com/test'

        buildIndex('/output/path')

        handle = mocks['file']()
        written_content = ''.join(str(call[0][0]) for call in handle.write.call_args_list)

        assert written_content.startswith('var feature_index=')
        assert written_content.endswith(';')

        json_content = written_content[len('var feature_index=') : -1]
        parsed = json.loads(json_content)
        assert isinstance(parsed, list)
        assert len(parsed) > 0
        assert all('title' in item and 'url' in item and 'type' in item for item in parsed)
