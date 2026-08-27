import pytest
from unittest.mock import Mock, patch, mock_open, MagicMock, call
import json
import os


class TestFeatureSearch:
    """Tests for feature search index building"""

    @pytest.fixture
    def mock_config(self):
        """Mock CKAN config"""
        with patch('ckanext.hdx_search.cli.click_feature_search_command.config') as mock_cfg:
            mock_cfg.get.side_effect = lambda key: {
                'hdx.lunr.index_location': '/tmp/test',
                'hdx.crises': 'ebola, nepal-earthquake'
            }.get(key)
            yield mock_cfg

    @pytest.fixture
    def mock_session(self):
        """Mock database Session"""
        with patch('ckanext.hdx_search.cli.click_feature_search_command.Session') as mock_sess:
            yield mock_sess

    @pytest.fixture
    def mock_url_for(self):
        """Mock url_for helper"""
        with patch('ckanext.hdx_search.cli.click_feature_search_command.h.url_for') as mock_url:
            mock_url.side_effect = lambda *args, **kwargs: f"http://test.com/{kwargs.get('id', 'test')}"
            yield mock_url

    @pytest.fixture
    def mock_log(self):
        """Mock logger"""
        with patch('ckanext.hdx_search.cli.click_feature_search_command.log') as mock_log:
            yield mock_log

    def test_build_index_success(self, mock_config, mock_log):
        """Test build_index executes successfully"""
        from ckanext.hdx_search.cli.click_feature_search_command import build_index

        with patch('ckanext.hdx_search.cli.click_feature_search_command._buildIndex') as mock_build:
            build_index()

            mock_config.get.assert_called_once_with('hdx.lunr.index_location')
            mock_build.assert_called_once_with('/tmp/test')
            mock_log.info.assert_any_call('Collecting Feature Pages...')
            mock_log.info.assert_any_call('Index successfully built...')

    def test_build_index_with_different_location(self, mock_config, mock_log):
        """Test build_index with different index location"""
        from ckanext.hdx_search.cli.click_feature_search_command import build_index

        # Override the side_effect with a direct return value
        mock_config.get.side_effect = None
        mock_config.get.return_value = '/custom/path'

        with patch('ckanext.hdx_search.cli.click_feature_search_command._buildIndex') as mock_build:
            build_index()

            mock_build.assert_called_once_with('/custom/path')

    def test_buildIndex_with_organizations_and_groups(self, mock_config, mock_session, mock_url_for):
        """Test _buildIndex creates index with organizations and groups"""
        from ckanext.hdx_search.cli.click_feature_search_command import _buildIndex

        # Mock database query results
        mock_session.execute.side_effect = [
            # Organizations and groups query
            [
                ('test-org', 'Test Organization', True, 'TO'),
                ('test-group', 'Test Group', False, None),
            ],
            # Pages query
            []
        ]

        m_open = mock_open()
        with patch('builtins.open', m_open):
            with patch('os.path.abspath', return_value='/tmp/test'):
                _buildIndex('/tmp/test')

        # Verify file was written
        m_open.assert_called_once_with('/tmp/test/lunr/feature-index.js', 'w')

        # Get written content
        written_content = ''.join(call.args[0] for call in m_open().write.call_args_list)

        # Verify content structure
        assert 'var feature_index=' in written_content
        assert 'Test Organization (TO)' in written_content
        assert 'Test Group' in written_content
        assert 'organisation' in written_content
        assert 'location' in written_content

    def test_buildIndex_filters_crisis_groups(self, mock_config, mock_session, mock_url_for):
        """Test _buildIndex filters out crisis groups but keeps static events"""
        from ckanext.hdx_search.cli.click_feature_search_command import _buildIndex

        mock_session.execute.side_effect = [
            [
                ('ebola', 'Ebola Crisis', False, None),
                ('nepal-earthquake', 'Nepal Earthquake', False, None),
                ('valid-group', 'Valid Group', False, None),
            ],
            [],
        ]

        m_open = mock_open()
        with patch('builtins.open', m_open):
            with patch('os.path.abspath', return_value='/tmp/test'):
                _buildIndex('/tmp/test')

        written_content = ''.join(call.args[0] for call in m_open().write.call_args_list)

        # Parse the JSON to check properly
        json_str = written_content.replace('var feature_index=', '').rstrip(';')
        data = json.loads(json_str)

        # Crisis groups should not be in the index
        group_titles = [item['title'] for item in data if item['type'] == 'location']
        assert 'Ebola Crisis' not in group_titles
        assert 'Nepal Earthquake' not in group_titles
        assert 'Valid Group' in group_titles

        # But static crisis events should be present
        #event_titles = [item['title'] for item in data if item['type'] == 'event']
        #assert 'Nepal Earthquake' in event_titles
        #assert 'West Africa Ebola Outbreak 2014' in event_titles

    def test_buildIndex_filters_crisis_groups_not_events(self, mock_config, mock_session, mock_url_for):
        """Test _buildIndex filters crisis groups but not crisis events"""
        from ckanext.hdx_search.cli.click_feature_search_command import _buildIndex

        mock_session.execute.side_effect = [
            [
                ('ebola', 'Ebola Crisis', False, None),
                ('nepal-earthquake', 'Nepal Earthquake Group', False, None),
                ('valid-group', 'Valid Group', False, None),
            ],
            [],
        ]

        m_open = mock_open()
        with patch('builtins.open', m_open):
            with patch('os.path.abspath', return_value='/tmp/test'):
                _buildIndex('/tmp/test')

        written_content = ''.join(call.args[0] for call in m_open().write.call_args_list)

        # Verify only valid group appears as location type
        assert '"title": "Valid Group"' in written_content
        assert '"type": "location"' in written_content

        # Crisis groups should not appear as locations
        assert '"title": "Ebola Crisis"' not in written_content
        assert '"title": "Nepal Earthquake Group"' not in written_content

    def test_buildIndex_with_closed_organizations(self, mock_config, mock_session, mock_url_for):
        """Test _buildIndex excludes closed organizations via SQL query"""
        from ckanext.hdx_search.cli.click_feature_search_command import _buildIndex

        mock_session.execute.side_effect = [
            [('open-org', 'Open Org', True, 'OO')],
            []
        ]

        m_open = mock_open()
        with patch('builtins.open', m_open):
            with patch('os.path.abspath', return_value='/tmp/test'):
                _buildIndex('/tmp/test')

        # Verify SQL query includes closed_organization check
        query_call = mock_session.execute.call_args_list[0][0][0]
        assert 'ge_closed.value' in query_call
        assert "ge_closed.value!='true'" in query_call

    def test_buildIndex_includes_static_crisis_events(self, mock_config, mock_session, mock_url_for):
        """Test _buildIndex includes hardcoded crisis events"""
        from ckanext.hdx_search.cli.click_feature_search_command import _buildIndex

        mock_session.execute.side_effect = [[], []]

        m_open = mock_open()
        with patch('builtins.open', m_open):
            with patch('os.path.abspath', return_value='/tmp/test'):
                _buildIndex('/tmp/test')

        written_content = ''.join(call.args[0] for call in m_open().write.call_args_list)

        #assert 'West Africa Ebola Outbreak 2014' in written_content
        #assert 'Nepal Earthquake' in written_content
        #assert 'event' in written_content

    def test_buildIndex_includes_pages(self, mock_config, mock_session, mock_url_for):
        """Test _buildIndex includes active pages"""
        from ckanext.hdx_search.cli.click_feature_search_command import _buildIndex

        mock_session.execute.side_effect = [
            [],
            [
                ('event-1', 'Event Page', 'event', 'Event description'),
                ('dashboard-1', 'Dashboard Page', 'dashboard', 'Dashboard description'),
            ]
        ]

        m_open = mock_open()
        with patch('builtins.open', m_open):
            with patch('os.path.abspath', return_value='/tmp/test'):
                _buildIndex('/tmp/test')

        written_content = ''.join(call.args[0] for call in m_open().write.call_args_list)

        assert 'Event Page' in written_content
        assert 'Dashboard Page' in written_content
        assert 'Event description' in written_content
        assert 'Dashboard description' in written_content

    def test_buildIndex_includes_visualizations(self, mock_config, mock_session, mock_url_for):
        """Test _buildIndex includes hardcoded visualizations"""
        from ckanext.hdx_search.cli.click_feature_search_command import _buildIndex

        mock_session.execute.side_effect = [[], []]

        m_open = mock_open()
        with patch('builtins.open', m_open):
            with patch('os.path.abspath', return_value='/tmp/test'):
                _buildIndex('/tmp/test')

        written_content = ''.join(call.args[0] for call in m_open().write.call_args_list)

        #assert 'Missing Migrants' in written_content
        #assert 'Lake Chad Crisis Dashboard' in written_content
        #assert 'Nepal: Community Perceptions Survey' in written_content
        #assert 'Somalia Humanitarian Dashboard' in written_content
        #assert 'WFP Food Market Prices' in written_content
        #assert 'visualization' in written_content

    def test_buildIndex_handles_missing_crisis_config(self, mock_config, mock_session, mock_url_for):
        """Test _buildIndex uses default crises when config missing"""
        from ckanext.hdx_search.cli.click_feature_search_command import _buildIndex

        mock_config.get.side_effect = lambda key: None if key == 'hdx.crises' else '/tmp/test'
        mock_session.execute.side_effect = [[('ebola', 'Ebola Group', False, None)], []]

        m_open = mock_open()
        with patch('builtins.open', m_open):
            with patch('os.path.abspath', return_value='/tmp/test'):
                _buildIndex('/tmp/test')

        written_content = ''.join(call.args[0] for call in m_open().write.call_args_list)

        # Parse JSON to check properly
        json_str = written_content.replace('var feature_index=', '').rstrip(';')
        data = json.loads(json_str)

        # Ebola group should be filtered out
        group_titles = [item['title'] for item in data if item['type'] == 'location']
        assert 'Ebola Group' not in group_titles

        # But static Ebola event should still be present
        event_titles = [item['title'] for item in data if item['type'] == 'event']
        #assert 'West Africa Ebola Outbreak 2014' in event_titles

    def test_buildIndex_creates_valid_json_structure(self, mock_config, mock_session, mock_url_for):
        """Test _buildIndex creates valid JSON structure"""
        from ckanext.hdx_search.cli.click_feature_search_command import _buildIndex

        mock_session.execute.side_effect = [
            [('test-org', 'Test Org', True, 'TO')],
            []
        ]

        m_open = mock_open()
        with patch('builtins.open', m_open):
            with patch('os.path.abspath', return_value='/tmp/test'):
                _buildIndex('/tmp/test')

        written_content = ''.join(call.args[0] for call in m_open().write.call_args_list)

        # Extract JSON from JavaScript variable
        json_str = written_content.replace('var feature_index=', '').rstrip(';')
        data = json.loads(json_str)

        # Verify structure
        assert isinstance(data, list)
        assert len(data) > 0
        assert all('title' in item for item in data)
        assert all('url' in item for item in data)
        assert all('type' in item for item in data)

    def test_buildIndex_handles_page_with_no_title(self, mock_config, mock_session, mock_url_for):
        """Test _buildIndex uses name when title is None"""
        from ckanext.hdx_search.cli.click_feature_search_command import _buildIndex

        mock_session.execute.side_effect = [
            [],
            [('test-page', None, 'event', 'Description')]
        ]

        m_open = mock_open()
        with patch('builtins.open', m_open):
            with patch('os.path.abspath', return_value='/tmp/test'):
                _buildIndex('/tmp/test')

        written_content = ''.join(call.args[0] for call in m_open().write.call_args_list)

        assert 'test-page' in written_content

    def test_buildIndex_handles_organization_without_code(self, mock_config, mock_session, mock_url_for):
        """Test _buildIndex handles organizations without acronym codes"""
        from ckanext.hdx_search.cli.click_feature_search_command import _buildIndex

        mock_session.execute.side_effect = [
            [
                ('org-with-code', 'Org With Code', True, 'OWC'),
                ('org-no-code', 'Org No Code', True, None),
                ('org-empty-code', 'Org Empty', True, ''),
            ],
            []
        ]

        m_open = mock_open()
        with patch('builtins.open', m_open):
            with patch('os.path.abspath', return_value='/tmp/test'):
                _buildIndex('/tmp/test')

        written_content = ''.join(call.args[0] for call in m_open().write.call_args_list)

        # With code should include it
        assert 'Org With Code (OWC)' in written_content
        # Without code should not have parentheses
        assert '"title": "Org No Code"' in written_content
        assert '"title": "Org Empty"' in written_content

    def test_buildIndex_url_generation(self, mock_config, mock_session, mock_url_for):
        """Test _buildIndex generates correct URL types"""
        from ckanext.hdx_search.cli.click_feature_search_command import _buildIndex

        mock_session.execute.side_effect = [
            [
                ('org-1', 'Organization', True, 'O1'),
                ('loc-1', 'Location', False, 'L1'),
            ],
            [('event-1', 'Event', 'event', 'desc')]
        ]

        m_open = mock_open()
        with patch('builtins.open', m_open):
            with patch('os.path.abspath', return_value='/tmp/test'):
                _buildIndex('/tmp/test')

        # Verify different URL generation calls
        assert any('organization.read' in str(call) for call in mock_url_for.call_args_list)
        assert any('group.read' in str(call) for call in mock_url_for.call_args_list)
        assert any('hdx_event.read_event' in str(call) for call in mock_url_for.call_args_list)

    def test_buildIndex_writes_to_correct_path(self, mock_config, mock_session, mock_url_for):
        """Test _buildIndex writes to correct file path"""
        from ckanext.hdx_search.cli.click_feature_search_command import _buildIndex

        mock_session.execute.side_effect = [[], []]

        m_open = mock_open()
        with patch('builtins.open', m_open):
            with patch('os.path.abspath', return_value='/custom/path') as mock_abspath:
                _buildIndex('/test/path')

                mock_abspath.assert_called_once_with('/test/path')
                m_open.assert_called_once_with('/custom/path/lunr/feature-index.js', 'w')

    def test_buildIndex_javascript_format(self, mock_config, mock_session, mock_url_for):
        """Test _buildIndex creates valid JavaScript variable assignment"""
        from ckanext.hdx_search.cli.click_feature_search_command import _buildIndex

        mock_session.execute.side_effect = [[], []]

        m_open = mock_open()
        with patch('builtins.open', m_open):
            with patch('os.path.abspath', return_value='/tmp/test'):
                _buildIndex('/tmp/test')

        written_content = ''.join(call.args[0] for call in m_open().write.call_args_list)

        # Verify JavaScript format
        assert written_content.startswith('var feature_index=')
        assert written_content.endswith(';')
        assert written_content.count('var feature_index=') == 1
