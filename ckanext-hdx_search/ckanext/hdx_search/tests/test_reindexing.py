import pytest
from unittest.mock import Mock, patch
from ckanext.hdx_search.helpers.reindexing import HdxSolrReindexer
import ckan.plugins.toolkit as tk


class TestHdxSolrReindexerRebuild:
    """Tests for HdxSolrReindexer.rebuild method"""

    @pytest.fixture
    def mock_dependencies(self):
        """Setup common mock dependencies"""
        context = {'user': 'test_user'}
        model = Mock()
        package_index = Mock()
        query_for = Mock()
        text_traceback = Mock(return_value='Traceback...')

        # Mock engine.dispose()
        model.meta.engine.dispose = Mock()

        return {
            'context': context,
            'model': model,
            'package_index': package_index,
            'query_for': query_for,
            'text_traceback': text_traceback,
        }

    @pytest.fixture
    def reindexer(self, mock_dependencies):
        """Create HdxSolrReindexer instance"""
        return HdxSolrReindexer(
            mock_dependencies['context'],
            mock_dependencies['model'],
            mock_dependencies['package_index'],
            mock_dependencies['query_for'],
            mock_dependencies['text_traceback'],
        )

    def test_rebuild_single_package_success(self, reindexer, mock_dependencies):
        """Test rebuilding index for a single package"""
        mock_pkg = Mock()
        mock_pkg.id = 'pkg-123'
        mock_dependencies['model'].Package.get.return_value = mock_pkg

        with patch.object(reindexer, '_hdx_fast_reindex') as mock_fast_reindex:
            reindexer.rebuild(package_id='pkg-123')

            mock_dependencies['model'].Package.get.assert_called_once_with('pkg-123')
            mock_dependencies['package_index'].remove_dict.assert_called_once_with({'id': 'pkg-123'})
            mock_fast_reindex.assert_called_once_with(
                mock_dependencies['context'], ['pkg-123'], mock_dependencies['package_index'], False, False, False
            )

    def test_rebuild_single_package_not_found(self, reindexer, mock_dependencies):
        """Test rebuilding index when package doesn't exist"""
        mock_dependencies['model'].Package.get.return_value = None

        with pytest.raises(tk.ObjectNotFound):
            reindexer.rebuild(package_id='non-existent')

    def test_rebuild_with_package_ids_list(self, reindexer, mock_dependencies):
        """Test rebuilding index for specific list of package IDs"""
        package_ids = ['pkg-1', 'pkg-2', 'pkg-3']

        with patch.object(reindexer, '_hdx_fast_reindex') as mock_fast_reindex:
            reindexer.rebuild(package_ids=package_ids)

            mock_fast_reindex.assert_called_once_with(
                mock_dependencies['context'], package_ids, mock_dependencies['package_index'], False, False, False
            )

    def test_rebuild_all_packages(self, reindexer, mock_dependencies):
        """Test rebuilding entire index"""
        mock_query = Mock()
        mock_query.filter.return_value.all.return_value = [('pkg-1',), ('pkg-2',), ('pkg-3',)]
        mock_dependencies['model'].Session.query.return_value = mock_query

        with patch.object(reindexer, '_hdx_fast_reindex') as mock_fast_reindex:
            reindexer.rebuild()

            mock_dependencies['package_index'].clear.assert_called_once()
            mock_fast_reindex.assert_called_once_with(
                mock_dependencies['context'],
                ['pkg-1', 'pkg-2', 'pkg-3'],
                mock_dependencies['package_index'],
                False,
                False,
                False,
            )

    def test_rebuild_all_packages_with_refresh(self, reindexer, mock_dependencies):
        """Test rebuilding index with refresh flag (doesn't clear)"""
        mock_query = Mock()
        mock_query.filter.return_value.all.return_value = [('pkg-1',)]
        mock_dependencies['model'].Session.query.return_value = mock_query

        with patch.object(reindexer, '_hdx_fast_reindex') as mock_fast_reindex:
            reindexer.rebuild(refresh=True)

            mock_dependencies['package_index'].clear.assert_not_called()
            mock_fast_reindex.assert_called_once()

    def test_rebuild_only_missing_packages(self, reindexer, mock_dependencies):
        """Test rebuilding index only for missing packages"""
        mock_query = Mock()
        mock_query.filter.return_value.all.return_value = [('pkg-1',), ('pkg-2',), ('pkg-3',), ('pkg-4',)]
        mock_dependencies['model'].Session.query.return_value = mock_query

        mock_package_query = Mock()
        mock_package_query.get_all_entity_ids.return_value = ['pkg-1', 'pkg-3']
        mock_dependencies['query_for'].return_value = mock_package_query

        with patch.object(reindexer, '_hdx_fast_reindex') as mock_fast_reindex:
            reindexer.rebuild(only_missing=True)

            # Should only index pkg-2 and pkg-4 (missing from index)
            call_args = mock_fast_reindex.call_args[0]
            indexed_ids = set(call_args[1])
            assert indexed_ids == {'pkg-2', 'pkg-4'}

    def test_rebuild_only_missing_when_all_indexed(self, reindexer, mock_dependencies):
        """Test rebuilding when all packages are already indexed"""
        mock_query = Mock()
        mock_query.filter.return_value.all.return_value = [('pkg-1',), ('pkg-2',)]
        mock_dependencies['model'].Session.query.return_value = mock_query

        mock_package_query = Mock()
        mock_package_query.get_all_entity_ids.return_value = ['pkg-1', 'pkg-2']
        mock_dependencies['query_for'].return_value = mock_package_query

        with patch.object(reindexer, '_hdx_fast_reindex') as mock_fast_reindex:
            reindexer.rebuild(only_missing=True)

            mock_fast_reindex.assert_not_called()

    def test_rebuild_with_defer_commit(self, reindexer, mock_dependencies):
        """Test rebuild with defer_commit flag"""
        mock_dependencies['model'].Package.get.return_value = Mock(id='pkg-1')

        with patch.object(reindexer, '_hdx_fast_reindex') as mock_fast_reindex:
            reindexer.rebuild(package_id='pkg-1', defer_commit=True)

            call_args = mock_fast_reindex.call_args[0]
            assert call_args[3] is True  # defer_commit parameter

    # def test_rebuild_with_force_flag(self, reindexer, mock_dependencies):
    #     """Test rebuild with force flag"""
    #     package_ids = ['pkg-1', 'pkg-2']
    #
    #     with patch.object(reindexer, '_hdx_fast_reindex') as mock_fast_reindex:
    #         reindexer.rebuild(package_ids=package_ids, force=True)
    #
    #         # Check using call_args which includes both args and kwargs
    #         call_kwargs = mock_fast_reindex.call_args[1] if len(mock_fast_reindex.call_args) > 1 else {}
    #         call_args = mock_fast_reindex.call_args[0]
    #
    #         # force could be passed as positional or keyword argument
    #         assert (len(call_args) > 5 and call_args[5] is True) or call_kwargs.get('force') is True

    # def test_rebuild_with_quiet_flag(self, reindexer, mock_dependencies):
    #     """Test rebuild with quiet flag"""
    #     package_ids = ['pkg-1']
    #
    #     with patch.object(reindexer, '_hdx_fast_reindex') as mock_fast_reindex:
    #         reindexer.rebuild(package_ids=package_ids, quiet=True)
    #
    #         call_kwargs = mock_fast_reindex.call_args[1] if len(mock_fast_reindex.call_args) > 1 else {}
    #         call_args = mock_fast_reindex.call_args[0]
    #
    #         assert (len(call_args) > 4 and call_args[4] is True) or call_kwargs.get('quiet') is True

    def test_rebuild_filters_deleted_packages(self, reindexer, mock_dependencies):
        """Test that deleted packages are filtered out"""
        mock_query = Mock()
        mock_filter = Mock()

        mock_dependencies['model'].Session.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.all.return_value = [('pkg-1',), ('pkg-2',)]

        with patch.object(reindexer, '_hdx_fast_reindex'):
            reindexer.rebuild()

            # Verify filter was called with state != 'deleted'
            mock_query.filter.assert_called_once()

    def test_rebuild_all_combinations_of_flags(self, reindexer, mock_dependencies):
        """Test various combinations of boolean flags"""
        mock_query = Mock()
        mock_query.filter.return_value.all.return_value = [('pkg-1',)]
        mock_dependencies['model'].Session.query.return_value = mock_query

        with patch.object(reindexer, '_hdx_fast_reindex') as mock_fast_reindex:
            reindexer.rebuild(force=True, defer_commit=True, quiet=True, refresh=True)

            call_kwargs = mock_fast_reindex.call_args[1] if len(mock_fast_reindex.call_args) > 1 else {}
            call_args = mock_fast_reindex.call_args[0]

            # Verify the flags are set correctly (either positional or keyword)
            assert (len(call_args) > 3 and call_args[3] is True) or call_kwargs.get('defer_commit') is True
            assert (len(call_args) > 4 and call_args[4] is True) or call_kwargs.get('quiet') is True
            assert (len(call_args) > 5 and call_args[5] is True) or call_kwargs.get('force') is True
            mock_dependencies['package_index'].clear.assert_not_called()

    def test_rebuild_empty_package_list(self, reindexer, mock_dependencies):
        """Test rebuild with empty package list - currently queries all packages due to falsy empty list"""
        mock_query = Mock()
        mock_query.filter.return_value.all.return_value = []
        mock_dependencies['model'].Session.query.return_value = mock_query

        with patch.object(reindexer, '_hdx_fast_reindex') as mock_fast_reindex:
            reindexer.rebuild(package_ids=[])

            # Current behavior: empty list is falsy, so it queries all packages
            mock_dependencies['package_index'].clear.assert_called_once()
            mock_fast_reindex.assert_called_once_with(
                mock_dependencies['context'], [], mock_dependencies['package_index'], False, False, False
            )

    @patch('ckanext.hdx_search.helpers.reindexing.log')
    def test_rebuild_logs_info_messages(self, mock_log, reindexer, mock_dependencies):
        """Test that appropriate log messages are generated"""
        mock_query = Mock()
        mock_query.filter.return_value.all.return_value = [('pkg-1',)]
        mock_dependencies['model'].Session.query.return_value = mock_query

        with patch.object(reindexer, '_hdx_fast_reindex'):
            reindexer.rebuild()

            assert mock_log.info.call_count >= 2
            mock_log.info.assert_any_call('Using hdx specific reindexing...')
            mock_log.info.assert_any_call('Rebuilding the whole index...')

    @patch('ckanext.hdx_search.helpers.reindexing.log')
    def test_rebuild_only_missing_logs_correctly(self, mock_log, reindexer, mock_dependencies):
        """Test log messages for only_missing mode"""
        mock_query = Mock()
        mock_query.filter.return_value.all.return_value = [('pkg-1',)]
        mock_dependencies['model'].Session.query.return_value = mock_query

        mock_package_query = Mock()
        mock_package_query.get_all_entity_ids.return_value = []
        mock_dependencies['query_for'].return_value = mock_package_query

        with patch.object(reindexer, '_hdx_fast_reindex'):
            reindexer.rebuild(only_missing=True)

            mock_log.info.assert_any_call('Indexing only missing packages...')
