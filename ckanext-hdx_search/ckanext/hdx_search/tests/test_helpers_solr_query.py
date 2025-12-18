import pytest
from ckanext.hdx_search.helpers.solr_query_helper import (
    generate_facet_query_from_list,
    generate_filter_query_from_list
)


class TestGenerateFilterQueryFromList:
    """Tests for generate_filter_query_from_list function"""

    def test_basic_or_query(self):
        """Test basic OR query generation"""
        result = generate_filter_query_from_list('tags', ['tag1', 'tag2', 'tag3'])
        assert result == 'tags: ("tag1" OR "tag2" OR "tag3")'

    def test_and_query(self):
        """Test AND query generation"""
        result = generate_filter_query_from_list('category', ['cat1', 'cat2'], boolean_operator='AND')
        assert result == 'category: ("cat1" AND "cat2")'

    def test_negated_query(self):
        """Test negated query generation"""
        result = generate_filter_query_from_list('status', ['draft', 'deleted'], negate=True)
        assert result == '-status: ("draft" OR "deleted")'

    def test_single_item(self):
        """Test query with single item"""
        result = generate_filter_query_from_list('type', ['dataset'])
        assert result == 'type: ("dataset")'

    def test_empty_list(self):
        """Test query with empty list"""
        result = generate_filter_query_from_list('tags', [])
        assert result == 'tags: ()'

    def test_items_with_spaces(self):
        """Test items containing spaces are properly quoted"""
        result = generate_filter_query_from_list('name', ['item one', 'item two'])
        assert result == 'name: ("item one" OR "item two")'

    def test_and_negated(self):
        """Test AND operator with negation"""
        result = generate_filter_query_from_list('field', ['val1', 'val2'], boolean_operator='AND', negate=True)
        assert result == '-field: ("val1" AND "val2")'


class TestGenerateFacetQueryFromList:
    """Tests for generate_facet_query_from_list function"""

    def test_basic_facet_query(self):
        """Test basic facet query generation"""
        result = generate_facet_query_from_list('Tag Filter', 'tag_filter', 'tags', ['tag1', 'tag2'])
        expected = '{!tag=tag_filter key="Tag Filter"}tags: ("tag1" OR "tag2")'
        assert result == expected

    def test_facet_query_with_and_operator(self):
        """Test facet query with AND operator"""
        result = generate_facet_query_from_list('Categories', 'cat_facet', 'category', ['cat1', 'cat2'], boolean_operator='AND')
        expected = '{!tag=cat_facet key="Categories"}category: ("cat1" AND "cat2")'
        assert result == expected

    def test_facet_query_negated(self):
        """Test negated facet query"""
        result = generate_facet_query_from_list('Exclude Status', 'status_ex', 'status', ['draft'], negate=True)
        expected = '{!tag=status_ex key="Exclude Status"}-status: ("draft")'
        assert result == expected

    def test_facet_query_single_item(self):
        """Test facet query with single item"""
        result = generate_facet_query_from_list('Type', 'type_facet', 'type', ['dataset'])
        expected = '{!tag=type_facet key="Type"}type: ("dataset")'
        assert result == expected

    def test_facet_query_empty_list(self):
        """Test facet query with empty list"""
        result = generate_facet_query_from_list('Empty', 'empty_tag', 'field', [])
        expected = '{!tag=empty_tag key="Empty"}field: ()'
        assert result == expected

    def generate_facet_query_from_list(title, query_tag, doc_property, item_list, boolean_operator='OR', negate=False):
        filter_query = generate_filter_query_from_list(doc_property, item_list, boolean_operator, negate)

        # Escape double quotes in title
        escaped_title = title.replace('"', '\\"')
        quoted_title = '"{}"'.format(escaped_title)
        extra_params = 'tag={} key={}'.format(query_tag, quoted_title)
        query = '{!' + extra_params + '}' + filter_query
        return query

    def test_facet_query_complex(self):
        """Test complex facet query with multiple parameters"""
        result = generate_facet_query_from_list(
            'Complex Filter',
            'complex_tag',
            'multi_field',
            ['item1', 'item2', 'item3'],
            boolean_operator='AND',
            negate=True
        )
        expected = '{!tag=complex_tag key="Complex Filter"}-multi_field: ("item1" AND "item2" AND "item3")'
        assert result == expected
