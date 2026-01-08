import pytest
from unittest.mock import Mock, patch

from ckanext.hdx_package.helpers.tag_recommender import TagRecommender, TagRecommenderTest


class TestTagRecommender:
    @pytest.fixture
    def sample_search_result(self):
        """Sample package_search result with facets"""
        return {
            'count': 10,
            'results': [{'id': 'dataset-1', 'name': 'test-dataset'}],
            'facets': {
                'vocab_Topics': {
                    'health': 5,
                    'education': 3,
                    'economy': 7,
                    'infrastructure': 2,
                }
            },
        }

    @pytest.fixture
    def sample_search_result_no_facets(self):
        """Sample package_search result without facets"""
        return {
            'count': 0,
            'results': [],
            'facets': {},
        }

    def test_init(self):
        """Test TagRecommender initialization"""
        recommender = TagRecommender(
            title='Test Dataset',
            organization='test-org',
            extra_fq='type:dataset',
            with_retry=False,
            facet_limit=20,
        )

        assert recommender.title == 'Test Dataset'
        assert recommender.organization == 'test-org'
        assert recommender.extra_fq == 'type:dataset'
        assert recommender.with_retry is False
        assert recommender.facet_limit == 20

    def test_init_defaults(self):
        """Test TagRecommender initialization with defaults"""
        recommender = TagRecommender(title='Test', organization='org')

        assert recommender.title == 'Test'
        assert recommender.organization == 'org'
        assert recommender.extra_fq is None
        assert recommender.with_retry is True
        assert recommender.facet_limit == TagRecommender.FACET_LIMIT

    @patch('ckanext.hdx_package.helpers.tag_recommender.get_action')
    def test_find_recommended_tags_success(self, mock_get_action, sample_search_result):
        """Test find_recommended_tags returns sorted tags"""
        mock_package_search = Mock(return_value=sample_search_result)
        mock_get_action.return_value = mock_package_search

        recommender = TagRecommender(title='Health Data', organization='WHO')
        result = recommender.find_recommended_tags()

        # Verify get_action was called correctly
        mock_get_action.assert_called_once_with('package_search')

        # Verify package_search was called with correct parameters
        call_args = mock_package_search.call_args[0][1]
        assert 'Health Data "WHO"' in call_args['q']
        assert call_args['rows'] == 1
        assert call_args['facet'] == 'on'
        assert 'vocab_Topics' in call_args['facet.field']
        assert call_args['facet.limit'] == TagRecommender.FACET_LIMIT

        # Verify results are sorted by count (descending)
        assert len(result) == 4
        assert result[0]['name'] == 'economy'
        assert result[0]['count'] == 7
        assert result[1]['name'] == 'health'
        assert result[1]['count'] == 5
        assert result[2]['name'] == 'education'
        assert result[2]['count'] == 3
        assert result[3]['name'] == 'infrastructure'
        assert result[3]['count'] == 2

    @patch('ckanext.hdx_package.helpers.tag_recommender.get_action')
    def test_find_recommended_tags_with_colon_in_title(self, mock_get_action, sample_search_result):
        """Test find_recommended_tags replaces colons in query"""
        mock_package_search = Mock(return_value=sample_search_result)
        mock_get_action.return_value = mock_package_search

        recommender = TagRecommender(title='Data: Health', organization='WHO')
        recommender.find_recommended_tags()

        call_args = mock_package_search.call_args[0][1]
        assert 'Data  Health "WHO"' in call_args['q']
        assert ':' not in call_args['q']

    @patch('ckanext.hdx_package.helpers.tag_recommender.get_action')
    def test_find_recommended_tags_with_extra_fq(self, mock_get_action, sample_search_result):
        """Test find_recommended_tags includes extra_fq parameter"""
        mock_package_search = Mock(return_value=sample_search_result)
        mock_get_action.return_value = mock_package_search

        recommender = TagRecommender(
            title='Test',
            organization='org',
            extra_fq='type:dataset -name:excluded',
        )
        recommender.find_recommended_tags()

        call_args = mock_package_search.call_args[0][1]
        assert 'fq' in call_args
        assert call_args['fq'] == 'type:dataset -name:excluded'

    @patch('ckanext.hdx_package.helpers.tag_recommender.get_action')
    def test_find_recommended_tags_no_facets(self, mock_get_action, sample_search_result_no_facets):
        """Test find_recommended_tags returns empty list when no facets"""
        mock_package_search = Mock(return_value=sample_search_result_no_facets)
        mock_get_action.return_value = mock_package_search

        recommender = TagRecommender(title='Test', organization='org')
        result = recommender.find_recommended_tags()

        assert result == []

    @patch('ckanext.hdx_package.helpers.tag_recommender.get_action')
    def test_find_recommended_tags_retry_when_few_results(self, mock_get_action):
        """Test find_recommended_tags retries without organization when results are few"""
        # First call returns only 2 tags
        first_result = {
            'facets': {'vocab_Topics': {'health': 5, 'education': 3}},
            'results': [],
        }
        # Second call (retry) returns more tags
        second_result = {
            'facets': {
                'vocab_Topics': {
                    'health': 10,
                    'education': 8,
                    'economy': 6,
                    'infrastructure': 4,
                }
            },
            'results': [],
        }

        mock_package_search = Mock(side_effect=[first_result, second_result])
        mock_get_action.return_value = mock_package_search

        recommender = TagRecommender(title='Health Data', organization='WHO', with_retry=True)
        result = recommender.find_recommended_tags()

        # Verify it was called twice
        assert mock_package_search.call_count == 2

        # First call includes organization
        first_call_args = mock_package_search.call_args_list[0][0][1]
        assert 'WHO' in first_call_args['q']

        # Second call excludes organization
        second_call_args = mock_package_search.call_args_list[1][0][1]
        assert 'WHO' not in second_call_args['q']

        # Returns results from second call
        assert len(result) == 4

    @patch('ckanext.hdx_package.helpers.tag_recommender.get_action')
    def test_find_recommended_tags_no_retry_when_disabled(self, mock_get_action):
        """Test find_recommended_tags doesn't retry when with_retry is False"""
        result_with_few_tags = {
            'facets': {'vocab_Topics': {'health': 5, 'education': 3}},
            'results': [],
        }

        mock_package_search = Mock(return_value=result_with_few_tags)
        mock_get_action.return_value = mock_package_search

        recommender = TagRecommender(title='Test', organization='org', with_retry=False)
        result = recommender.find_recommended_tags()

        # Verify it was called only once
        assert mock_package_search.call_count == 1
        assert len(result) == 2

    @patch('ckanext.hdx_package.helpers.tag_recommender.get_action')
    def test_find_recommended_tags_no_retry_when_more_than_two_results(self, mock_get_action):
        """Test find_recommended_tags doesn't retry when 3+ results"""
        result_with_many_tags = {
            'facets': {'vocab_Topics': {'health': 5, 'education': 3, 'economy': 2}},
            'results': [],
        }

        mock_package_search = Mock(return_value=result_with_many_tags)
        mock_get_action.return_value = mock_package_search

        recommender = TagRecommender(title='Test', organization='org', with_retry=True)
        result = recommender.find_recommended_tags()

        # Verify it was called only once
        assert mock_package_search.call_count == 1
        assert len(result) == 3

    @patch('ckanext.hdx_package.helpers.tag_recommender.get_action')
    def test_find_recommended_tags_no_title(self, mock_get_action):
        """Test find_recommended_tags returns empty list when no title"""
        recommender = TagRecommender(title='', organization='org')
        result = recommender.find_recommended_tags()

        mock_get_action.assert_not_called()
        assert result == []

    @patch('ckanext.hdx_package.helpers.tag_recommender.get_action')
    def test_find_recommended_tags_custom_facet_limit(self, mock_get_action, sample_search_result):
        """Test find_recommended_tags uses custom facet_limit"""
        mock_package_search = Mock(return_value=sample_search_result)
        mock_get_action.return_value = mock_package_search

        recommender = TagRecommender(title='Test', organization='org', facet_limit=25)
        recommender.find_recommended_tags()

        call_args = mock_package_search.call_args[0][1]
        assert call_args['facet.limit'] == 25

    @patch('ckanext.hdx_package.helpers.tag_recommender.get_action')
    def test_find_recommended_tags_no_organization(self, mock_get_action, sample_search_result):
        """Test find_recommended_tags without organization"""
        mock_package_search = Mock(return_value=sample_search_result)
        mock_get_action.return_value = mock_package_search

        recommender = TagRecommender(title='Health Data', organization=None)
        recommender.find_recommended_tags()

        call_args = mock_package_search.call_args[0][1]
        assert call_args['q'] == 'Health Data'


class TestTagRecommenderTest:
    @pytest.fixture
    def sample_packages(self):
        """Sample package search results"""
        return [
            {
                'title': 'Health Dataset',
                'name': 'health-dataset',
                'organization': {'name': 'who'},
                'tags': [
                    {'name': 'health', 'vocabulary_id': 'vocab-1'},
                    {'name': 'covid', 'vocabulary_id': 'vocab-1'},
                ],
            },
            {
                'title': 'Education Dataset',
                'name': 'education-dataset',
                'organization': {'name': 'unesco'},
                'tags': [
                    {'name': 'education', 'vocabulary_id': 'vocab-1'},
                    {'name': 'schools', 'vocabulary_id': 'vocab-1'},
                    {'name': 'literacy', 'vocabulary_id': 'vocab-1'},
                ],
            },
        ]

    def test_init_defaults(self):
        """Test TagRecommenderTest initialization with defaults"""
        tester = TagRecommenderTest()

        assert tester.limit == TagRecommenderTest.LIMIT
        assert tester.page == 1
        assert tester.just_percentage is False
        assert tester.with_retry is True
        assert tester.all is False
        assert tester.facet_limit == TagRecommender.FACET_LIMIT
        assert tester.dataset_name is None

    def test_init_custom_values(self):
        """Test TagRecommenderTest initialization with custom values"""
        tester = TagRecommenderTest(
            limit='50',
            page='2',
            just_percentage='true',
            with_retry='false',
            all='false',
            facet_limit='25',
            dataset_name='test-dataset',
        )

        assert tester.limit == 50
        assert tester.page == 2
        assert tester.just_percentage is True
        assert tester.with_retry is False
        assert tester.all is False
        assert tester.facet_limit == 25
        assert tester.dataset_name == 'test-dataset'

    def test_init_all_mode(self):
        """Test TagRecommenderTest initialization with all=true"""
        tester = TagRecommenderTest(limit='50', all='true')

        assert tester.limit == TagRecommenderTest.LIMIT
        assert tester.all is True
        assert tester.just_percentage is True

    @patch('ckanext.hdx_package.helpers.tag_recommender.get_action')
    def test_find_packages(self, mock_get_action, sample_packages):
        """Test find_packages returns simplified package data"""
        mock_package_search = Mock(
            return_value={
                'results': sample_packages,
                'count': 2,
            }
        )
        mock_get_action.return_value = mock_package_search

        tester = TagRecommenderTest(limit='10', page='1')
        results, total = tester.find_packages(page=1)

        # Verify get_action was called
        mock_get_action.assert_called_once_with('package_search')

        # Verify package_search was called with correct parameters
        call_args = mock_package_search.call_args[0][1]
        assert call_args['rows'] == 10
        assert call_args['start'] == 0
        assert call_args['q'] == ''

        # Verify results format
        assert len(results) == 2
        assert results[0]['title'] == 'Health Dataset'
        assert results[0]['name'] == 'health-dataset'
        assert results[0]['organization'] == 'who'
        assert results[0]['tags'] == ['health', 'covid']

        assert results[1]['title'] == 'Education Dataset'
        assert results[1]['tags'] == ['education', 'schools', 'literacy']

        assert total == 2

    @patch('ckanext.hdx_package.helpers.tag_recommender.get_action')
    def test_find_packages_with_dataset_name_filter(self, mock_get_action):
        """Test find_packages with dataset_name filter"""
        mock_package_search = Mock(return_value={'results': [], 'count': 0})
        mock_get_action.return_value = mock_package_search

        tester = TagRecommenderTest(dataset_name='specific-dataset')
        tester.find_packages(page=1)

        call_args = mock_package_search.call_args[0][1]
        assert 'fq' in call_args
        assert call_args['fq'] == 'name:specific-dataset'

    @patch('ckanext.hdx_package.helpers.tag_recommender.get_action')
    def test_find_packages_pagination(self, mock_get_action):
        """Test find_packages pagination calculation"""
        mock_package_search = Mock(return_value={'results': [], 'count': 0})
        mock_get_action.return_value = mock_package_search

        tester = TagRecommenderTest(limit='50', page='3')
        tester.find_packages(page=3)

        call_args = mock_package_search.call_args[0][1]
        assert call_args['rows'] == 50
        assert call_args['start'] == 100  # (page 3 - 1) * 50

    @patch('ckanext.hdx_package.helpers.tag_recommender.get_action')
    def test_find_packages_no_tags(self, mock_get_action):
        """Test find_packages with datasets without tags"""
        packages = [
            {
                'title': 'No Tags Dataset',
                'name': 'no-tags',
                'organization': {'name': 'org'},
            }
        ]
        mock_package_search = Mock(return_value={'results': packages, 'count': 1})
        mock_get_action.return_value = mock_package_search

        tester = TagRecommenderTest()
        results, total = tester.find_packages(page=1)

        assert len(results) == 1
        assert results[0]['tags'] == []

    @patch('ckanext.hdx_package.helpers.tag_recommender.get_action')
    def test_find_packages_filters_non_vocab_tags(self, mock_get_action):
        """Test find_packages filters out tags without vocabulary_id"""
        packages = [
            {
                'title': 'Mixed Tags Dataset',
                'name': 'mixed-tags',
                'organization': {'name': 'org'},
                'tags': [
                    {'name': 'vocab-tag', 'vocabulary_id': 'vocab-1'},
                    {'name': 'normal-tag'},  # No vocabulary_id
                    {'name': 'another-vocab-tag', 'vocabulary_id': 'vocab-1'},
                ],
            }
        ]
        mock_package_search = Mock(return_value={'results': packages, 'count': 1})
        mock_get_action.return_value = mock_package_search

        tester = TagRecommenderTest()
        results, total = tester.find_packages(page=1)

        # Only vocabulary tags should be included
        assert results[0]['tags'] == ['vocab-tag', 'another-vocab-tag']

    @patch('ckanext.hdx_package.helpers.tag_recommender.TagRecommender')
    @patch('ckanext.hdx_package.helpers.tag_recommender.get_action')
    def test_run_test_calculates_percentage(self, mock_get_action, mock_tag_recommender):
        """Test run_test calculates correct percentage"""
        packages = [
            {
                'title': 'Dataset 1',
                'name': 'dataset-1',
                'organization': {'name': 'org1'},
                'tags': [
                    {'name': 'health', 'vocabulary_id': 'vocab-1'},
                    {'name': 'education', 'vocabulary_id': 'vocab-1'},
                ],
            }
        ]
        mock_package_search = Mock(return_value={'results': packages, 'count': 1})
        mock_get_action.return_value = mock_package_search

        # Mock TagRecommender to return matching tags
        mock_recommender_instance = Mock()
        mock_recommender_instance.find_recommended_tags.return_value = [
            {'name': 'health', 'count': 10},
            {'name': 'economy', 'count': 5},
        ]
        mock_tag_recommender.return_value = mock_recommender_instance

        tester = TagRecommenderTest(limit='10')
        result = tester.run_test()

        # 1 out of 2 tags found = 50%
        assert result['pecentage_found'] == 50.0
        assert 'datasets' in result
        assert result['datasets'][0]['percentage_found'] == 50.0

    @patch('ckanext.hdx_package.helpers.tag_recommender.TagRecommender')
    @patch('ckanext.hdx_package.helpers.tag_recommender.get_action')
    def test_run_test_just_percentage(self, mock_get_action, mock_tag_recommender):
        """Test run_test with just_percentage returns only percentage"""
        packages = [
            {
                'title': 'Dataset 1',
                'name': 'dataset-1',
                'organization': {'name': 'org1'},
                'tags': [{'name': 'health', 'vocabulary_id': 'vocab-1'}],
            }
        ]
        mock_package_search = Mock(return_value={'results': packages, 'count': 1})
        mock_get_action.return_value = mock_package_search

        mock_recommender_instance = Mock()
        mock_recommender_instance.find_recommended_tags.return_value = [{'name': 'health', 'count': 10}]
        mock_tag_recommender.return_value = mock_recommender_instance

        tester = TagRecommenderTest(just_percentage='true')
        result = tester.run_test()

        assert 'pecentage_found' in result
        assert 'datasets' not in result

    @patch('ckanext.hdx_package.helpers.tag_recommender.TagRecommender')
    @patch('ckanext.hdx_package.helpers.tag_recommender.get_action')
    def test_run_test_no_tags(self, mock_get_action, mock_tag_recommender):
        """Test run_test with dataset without tags"""
        packages = [
            {
                'title': 'No Tags Dataset',
                'name': 'no-tags',
                'organization': {'name': 'org'},
            }
        ]
        mock_package_search = Mock(return_value={'results': packages, 'count': 1})
        mock_get_action.return_value = mock_package_search

        mock_recommender_instance = Mock()
        mock_recommender_instance.find_recommended_tags.return_value = []
        mock_tag_recommender.return_value = mock_recommender_instance

        tester = TagRecommenderTest()
        result = tester.run_test()

        # No tags means no percentage calculation for that dataset
        assert result['pecentage_found'] == 0

    @patch('ckanext.hdx_package.helpers.tag_recommender.TagRecommender')
    @patch('ckanext.hdx_package.helpers.tag_recommender.get_action')
    def test_run_test_multiple_datasets(self, mock_get_action, mock_tag_recommender):
        """Test run_test calculates average across multiple datasets"""
        packages = [
            {
                'title': 'Dataset 1',
                'name': 'dataset-1',
                'organization': {'name': 'org1'},
                'tags': [
                    {'name': 'health', 'vocabulary_id': 'vocab-1'},
                    {'name': 'education', 'vocabulary_id': 'vocab-1'},
                ],
            },
            {
                'title': 'Dataset 2',
                'name': 'dataset-2',
                'organization': {'name': 'org2'},
                'tags': [
                    {'name': 'economy', 'vocabulary_id': 'vocab-1'},
                    {'name': 'trade', 'vocabulary_id': 'vocab-1'},
                ],
            },
        ]
        mock_package_search = Mock(return_value={'results': packages, 'count': 2})
        mock_get_action.return_value = mock_package_search

        # First dataset: 1/2 = 50%, Second dataset: 2/2 = 100%
        mock_recommender_instance = Mock()
        mock_recommender_instance.find_recommended_tags.side_effect = [
            [{'name': 'health', 'count': 10}],
            [{'name': 'economy', 'count': 8}, {'name': 'trade', 'count': 6}],
        ]
        mock_tag_recommender.return_value = mock_recommender_instance

        tester = TagRecommenderTest()
        result = tester.run_test()

        # Average: (50 + 100) / 2 = 75
        assert result['pecentage_found'] == 75.0

    @patch('ckanext.hdx_package.helpers.tag_recommender.TagRecommender')
    @patch('ckanext.hdx_package.helpers.tag_recommender.get_action')
    def test_run_test_all_mode_multiple_pages(self, mock_get_action, mock_tag_recommender):
        """Test run_test in all mode processes multiple pages"""
        # First page
        first_page = [
            {
                'title': 'Dataset 1',
                'name': 'dataset-1',
                'organization': {'name': 'org1'},
                'tags': [{'name': 'health', 'vocabulary_id': 'vocab-1'}],
            }
        ]
        # Second page
        second_page = [
            {
                'title': 'Dataset 2',
                'name': 'dataset-2',
                'organization': {'name': 'org2'},
                'tags': [{'name': 'education', 'vocabulary_id': 'vocab-1'}],
            }
        ]

        mock_package_search = Mock()
        mock_package_search.side_effect = [
            {'results': first_page, 'count': 150},  # Total > limit, triggers page 2
            {'results': second_page, 'count': 150},
        ]
        mock_get_action.return_value = mock_package_search

        mock_recommender_instance = Mock()
        mock_recommender_instance.find_recommended_tags.return_value = [{'name': 'health', 'count': 10}]
        mock_tag_recommender.return_value = mock_recommender_instance

        tester = TagRecommenderTest(all='true')
        result = tester.run_test()

        # Verify both pages were processed
        assert mock_package_search.call_count == 2
        # In all mode, just_percentage is True, so only percentage is returned
        assert 'pecentage_found' in result
        assert 'datasets' not in result

    @patch('ckanext.hdx_package.helpers.tag_recommender.TagRecommender')
    @patch('ckanext.hdx_package.helpers.tag_recommender.get_action')
    def test_run_test_passes_extra_fq(self, mock_get_action, mock_tag_recommender):
        """Test run_test passes extra_fq to TagRecommender"""
        packages = [
            {
                'title': 'Dataset 1',
                'name': 'dataset-1',
                'organization': {'name': 'org1'},
                'tags': [{'name': 'health', 'vocabulary_id': 'vocab-1'}],
            }
        ]
        mock_package_search = Mock(return_value={'results': packages, 'count': 1})
        mock_get_action.return_value = mock_package_search

        mock_recommender_instance = Mock()
        mock_recommender_instance.find_recommended_tags.return_value = []
        mock_tag_recommender.return_value = mock_recommender_instance

        tester = TagRecommenderTest()
        tester.run_test()

        # Verify TagRecommender was called with extra_fq parameter
        call_kwargs = mock_tag_recommender.call_args[1]
        assert 'extra_fq' in call_kwargs
        assert call_kwargs['extra_fq'] == 'type:dataset -name:dataset-1'
