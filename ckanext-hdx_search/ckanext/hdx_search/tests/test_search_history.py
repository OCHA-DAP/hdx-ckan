from unittest.mock import Mock, patch
from datetime import datetime
from ckanext.hdx_search.helpers.search_history import num_of_results_for_prev_searches


class TestNumOfResultsForPrevSearches:
    """Tests for num_of_results_for_prev_searches function"""

    @patch('ckanext.hdx_search.helpers.search_history.SearchedString')
    @patch('ckanext.hdx_search.helpers.search_history._get_action')
    @patch('ckanext.hdx_search.helpers.search_history.h')
    def test_no_user_returns_empty_list(self, mock_h, mock_get_action, mock_searched_string):
        """Test that None user returns empty list"""
        result = num_of_results_for_prev_searches(None)
        assert result == []
        mock_searched_string.latest_queries_for_user.assert_not_called()

    @patch('ckanext.hdx_search.helpers.search_history.SearchedString')
    @patch('ckanext.hdx_search.helpers.search_history._get_action')
    @patch('ckanext.hdx_search.helpers.search_history.h')
    def test_user_without_id_returns_empty_list(self, mock_h, mock_get_action, mock_searched_string):
        """Test that user without id returns empty list"""
        mock_user = Mock()
        mock_user.id = None
        result = num_of_results_for_prev_searches(mock_user)
        assert result == []
        mock_searched_string.latest_queries_for_user.assert_not_called()

    @patch('ckanext.hdx_search.helpers.search_history.SearchedString')
    @patch('ckanext.hdx_search.helpers.search_history._get_action')
    @patch('ckanext.hdx_search.helpers.search_history.h')
    def test_no_previous_searches_returns_empty_list(self, mock_h, mock_get_action, mock_searched_string):
        """Test that user with no previous searches returns empty list"""
        mock_user = Mock()
        mock_user.id = 'user-123'
        mock_user.name = 'test_user'

        mock_searched_string.latest_queries_for_user.return_value = []

        result = num_of_results_for_prev_searches(mock_user)
        assert result == []
        mock_searched_string.latest_queries_for_user.assert_called_once_with('user-123')

    @patch('ckanext.hdx_search.helpers.search_history.SearchedString')
    @patch('ckanext.hdx_search.helpers.search_history._get_action')
    @patch('ckanext.hdx_search.helpers.search_history.h')
    def test_single_search_with_results(self, mock_h, mock_get_action, mock_searched_string):
        """Test single search query with results"""
        mock_user = Mock()
        mock_user.id = 'user-123'
        mock_user.name = 'test_user'

        mock_search = Mock()
        mock_search.search_string = 'test query'
        mock_search.last_modified = datetime(2024, 1, 1, 12, 0, 0)

        mock_searched_string.latest_queries_for_user.return_value = [mock_search]

        mock_package_search = Mock(return_value={'count': 5})
        mock_get_action.return_value = mock_package_search

        mock_h.url_for.return_value = 'http://example.com/search'

        result = num_of_results_for_prev_searches(mock_user)

        assert len(result) == 1
        assert result[0]['text'] == 'test query'
        assert result[0]['count'] == 5
        assert result[0]['url'] == 'http://example.com/search'

    @patch('ckanext.hdx_search.helpers.search_history.SearchedString')
    @patch('ckanext.hdx_search.helpers.search_history._get_action')
    @patch('ckanext.hdx_search.helpers.search_history.h')
    def test_multiple_searches_with_results(self, mock_h, mock_get_action, mock_searched_string):
        """Test multiple search queries with results"""
        mock_user = Mock()
        mock_user.id = 'user-123'
        mock_user.name = 'test_user'

        mock_searches = []
        for i in range(3):
            mock_search = Mock()
            mock_search.search_string = f'query {i}'
            mock_search.last_modified = datetime(2024, 1, i + 1, 12, 0, 0)
            mock_searches.append(mock_search)

        mock_searched_string.latest_queries_for_user.return_value = mock_searches

        mock_package_search = Mock(side_effect=[{'count': 10}, {'count': 5}, {'count': 3}])
        mock_get_action.return_value = mock_package_search

        mock_h.url_for.return_value = 'http://example.com/search'

        result = num_of_results_for_prev_searches(mock_user)

        assert len(result) == 3
        assert result[0]['text'] == 'query 0'
        assert result[0]['count'] == 10
        assert result[1]['text'] == 'query 1'
        assert result[1]['count'] == 5
        assert result[2]['text'] == 'query 2'
        assert result[2]['count'] == 3

    @patch('ckanext.hdx_search.helpers.search_history.SearchedString')
    @patch('ckanext.hdx_search.helpers.search_history._get_action')
    @patch('ckanext.hdx_search.helpers.search_history.h')
    def test_filters_zero_count_results(self, mock_h, mock_get_action, mock_searched_string):
        """Test that searches with zero results are filtered out"""
        mock_user = Mock()
        mock_user.id = 'user-123'
        mock_user.name = 'test_user'

        mock_searches = []
        for i in range(3):
            mock_search = Mock()
            mock_search.search_string = f'query {i}'
            mock_search.last_modified = datetime(2024, 1, i + 1, 12, 0, 0)
            mock_searches.append(mock_search)

        mock_searched_string.latest_queries_for_user.return_value = mock_searches

        mock_package_search = Mock(side_effect=[{'count': 0}, {'count': 5}, {'count': 0}])
        mock_get_action.return_value = mock_package_search

        mock_h.url_for.return_value = 'http://example.com/search'

        result = num_of_results_for_prev_searches(mock_user)

        assert len(result) == 1
        assert result[0]['text'] == 'query 1'
        assert result[0]['count'] == 5

    @patch('ckanext.hdx_search.helpers.search_history.SearchedString')
    @patch('ckanext.hdx_search.helpers.search_history._get_action')
    @patch('ckanext.hdx_search.helpers.search_history.h')
    def test_limits_to_three_results(self, mock_h, mock_get_action, mock_searched_string):
        """Test that results are limited to 3"""
        mock_user = Mock()
        mock_user.id = 'user-123'
        mock_user.name = 'test_user'

        mock_searches = []
        for i in range(5):
            mock_search = Mock()
            mock_search.search_string = f'query {i}'
            mock_search.last_modified = datetime(2024, 1, i + 1, 12, 0, 0)
            mock_searches.append(mock_search)

        mock_searched_string.latest_queries_for_user.return_value = mock_searches

        mock_package_search = Mock(return_value={'count': 10})
        mock_get_action.return_value = mock_package_search

        mock_h.url_for.return_value = 'http://example.com/search'

        result = num_of_results_for_prev_searches(mock_user)

        assert len(result) == 3

    @patch('ckanext.hdx_search.helpers.search_history.SearchedString')
    @patch('ckanext.hdx_search.helpers.search_history._get_action')
    @patch('ckanext.hdx_search.helpers.search_history.h')
    @patch('ckanext.hdx_search.helpers.search_history.log')
    def test_handles_package_search_exception(self, mock_log, mock_h, mock_get_action, mock_searched_string):
        """Test that exceptions in package_search are handled gracefully"""
        mock_user = Mock()
        mock_user.id = 'user-123'
        mock_user.name = 'test_user'

        mock_search = Mock()
        mock_search.search_string = 'test query'
        mock_search.last_modified = datetime(2024, 1, 1, 12, 0, 0)

        mock_searched_string.latest_queries_for_user.return_value = [mock_search]

        mock_package_search = Mock(side_effect=Exception('Search error'))
        mock_get_action.return_value = mock_package_search

        result = num_of_results_for_prev_searches(mock_user)

        assert result == []
        mock_log.error.assert_called_once()

    @patch('ckanext.hdx_search.helpers.search_history.SearchedString')
    @patch('ckanext.hdx_search.helpers.search_history._get_action')
    @patch('ckanext.hdx_search.helpers.search_history.h')
    def test_correct_context_and_data_dict(self, mock_h, mock_get_action, mock_searched_string):
        """Test that correct context and data_dict are passed to package_search"""
        mock_user = Mock()
        mock_user.id = 'user-123'
        mock_user.name = 'test_user'

        mock_search = Mock()
        mock_search.search_string = 'test query'
        mock_search.last_modified = datetime(2024, 1, 1, 12, 30, 45)

        mock_searched_string.latest_queries_for_user.return_value = [mock_search]

        mock_package_search = Mock(return_value={'count': 5})
        mock_get_action.return_value = mock_package_search

        mock_h.url_for.return_value = 'http://example.com/search'

        num_of_results_for_prev_searches(mock_user)

        call_args = mock_package_search.call_args
        context = call_args[0][0]
        data_dict = call_args[0][1]

        assert context['user'] == 'test_user'
        assert context['auth_user_obj'] == mock_user
        assert data_dict['q'] == 'test query'
        assert data_dict['fq'] == 'metadata_modified:[2024-01-01T12:30:45Z TO NOW]'
        assert data_dict['rows'] == 1
        assert data_dict['start'] == 0

    @patch('ckanext.hdx_search.helpers.search_history.SearchedString')
    @patch('ckanext.hdx_search.helpers.search_history._get_action')
    @patch('ckanext.hdx_search.helpers.search_history.h')
    def test_url_generation_parameters(self, mock_h, mock_get_action, mock_searched_string):
        """Test that URL is generated with correct parameters"""
        mock_user = Mock()
        mock_user.id = 'user-123'
        mock_user.name = 'test_user'

        mock_search = Mock()
        mock_search.search_string = 'test query'
        mock_search.last_modified = datetime(2024, 1, 1, 12, 30, 45)

        mock_searched_string.latest_queries_for_user.return_value = [mock_search]

        mock_package_search = Mock(return_value={'count': 5})
        mock_get_action.return_value = mock_package_search

        mock_h.url_for.return_value = 'http://example.com/search'

        num_of_results_for_prev_searches(mock_user)

        mock_h.url_for.assert_called_once_with(
            'hdx_dataset.search',
            ext_after_metadata_modified='2024-01-01T12:30:45Z',
            ext_search_source='main-nav',
            q='test query',
        )
