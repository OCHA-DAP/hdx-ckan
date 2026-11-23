from ckanext.hdx_package.helpers.constants import COD_GROUP_EXPLANATION_LINK
from ckanext.hdx_search.controller_logic.search_logic import SearchLogic


def _create_featured_cod_facet_category(cod_category):
    # private (name-mangled) builder of the "CODs" group in the Advanced filters
    return SearchLogic()._SearchLogic__create_featured_cod_facet_category(cod_category)


def _cod_item(name, count, selected=False):
    return {'name': name, 'display_name': name, 'count': count, 'selected': selected, 'category_key': 'cod_level'}


class TestCodFacetCategory:
    def test_children_names_order_and_counts(self):
        category = _create_featured_cod_facet_category({
            'name': 'cod_level',
            'display_name': 'CODs',
            'items': [
                _cod_item('cod-ps', 149),
                _cod_item('not-cod', 7),
                _cod_item('cod-ab', 165),
            ],
        })

        assert [item['name'] for item in category['items']] == ['cod-ab', 'cod-ps']
        assert [item['display_name'] for item in category['items']] == ['COD Admin Boundaries',
                                                                         'COD Population Stats']
        assert all(not item.get('explanation') for item in category['items'])
        assert category['name'] == 'ALL'
        assert category['category_key'] == 'cod_level'
        assert category['count'] == 314
        assert category['selected'] is False
        assert category['explanation_link'] == COD_GROUP_EXPLANATION_LINK == 'https://docs.humdata.org/about/cod'

    def test_old_values_are_not_listed(self):
        category = _create_featured_cod_facet_category({
            'name': 'cod_level',
            'display_name': 'CODs',
            'items': [
                _cod_item('cod-standard', 92),
                _cod_item('cod-enhanced', 222),
                _cod_item('cod-candidate', 1),
            ],
        })

        assert category['items'] == []
        assert category['count'] == 0
        assert category['selected'] is False

    def test_selected_only_when_all_children_selected(self):
        category = _create_featured_cod_facet_category({
            'name': 'cod_level',
            'display_name': 'CODs',
            'items': [_cod_item('cod-ab', 165, selected=True), _cod_item('cod-ps', 149, selected=True)],
        })
        assert category['selected'] is True

        category = _create_featured_cod_facet_category({
            'name': 'cod_level',
            'display_name': 'CODs',
            'items': [_cod_item('cod-ab', 165, selected=True), _cod_item('cod-ps', 149)],
        })
        assert category['selected'] is False
