"""
Unit tests for hdx_get_locations helper.

cached_group_list is mocked so no DB or plugin stack is required.
"""

from unittest.mock import patch, MagicMock

import ckanext.hdx_theme.helpers.helpers as hdx_helpers

# ---------------------------------------------------------------------------
# Fixtures / shared test data
# ---------------------------------------------------------------------------

_MOCK_GROUPS = [
    {
        'id': '1',
        'name': 'afghanistan',
        'display_name': 'Afghanistan',
        'package_count': 10,
        'activity_level': 'active',
    },
    {
        'id': '2',
        'name': 'zimbabwe',
        'display_name': 'Zimbabwe',
        'package_count': 5,
        'activity_level': 'inactive',
    },
    {
        'id': '3',
        'name': 'burundi',
        'display_name': 'Burundi',
        'package_count': 3,
        'activity_level': 'active',
    },
    {
        'id': '4',
        'name': 'chad',
        'display_name': 'Chad',
        'package_count': 0,
        'activity_level': 'inactive',
    },
]


def _make_cached_group_list_action(groups):
    """Return a mock suitable for logic.get_action('cached_group_list')."""
    action_fn = MagicMock(return_value=groups)
    get_action_mock = MagicMock(return_value=action_fn)
    return get_action_mock


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestHdxGetLocations:

    def _call(self, groups, hrp=None):
        """Helper: patch cached_group_list and call hdx_get_locations."""
        with patch(
            'ckanext.hdx_theme.helpers.helpers.logic.get_action',
            _make_cached_group_list_action(groups),
        ):
            return hdx_helpers.hdx_get_locations(hrp=hrp)

    # --- hrp=None: returns all locations ---

    def test_no_filter_returns_all_locations(self):
        result = self._call(_MOCK_GROUPS)
        assert len(result) == len(_MOCK_GROUPS)

    def test_no_filter_result_contains_hrp_field(self):
        result = self._call(_MOCK_GROUPS)
        for item in result:
            assert 'hrp' in item

    def test_no_filter_hrp_true_when_activity_level_active(self):
        result = self._call(_MOCK_GROUPS)
        by_name = {r['name']: r for r in result}
        assert by_name['afghanistan']['hrp'] is True
        assert by_name['burundi']['hrp'] is True

    def test_no_filter_hrp_false_when_activity_level_inactive(self):
        result = self._call(_MOCK_GROUPS)
        by_name = {r['name']: r for r in result}
        assert by_name['zimbabwe']['hrp'] is False
        assert by_name['chad']['hrp'] is False

    # --- hrp=True: only active locations ---

    def test_hrp_true_returns_only_active_locations(self):
        result = self._call(_MOCK_GROUPS, hrp=True)
        assert all(r['hrp'] is True for r in result)

    def test_hrp_true_excludes_inactive_locations(self):
        result = self._call(_MOCK_GROUPS, hrp=True)
        names = [r['name'] for r in result]
        assert 'zimbabwe' not in names
        assert 'chad' not in names

    def test_hrp_true_count(self):
        result = self._call(_MOCK_GROUPS, hrp=True)
        active_count = sum(1 for g in _MOCK_GROUPS if g['activity_level'] == 'active')
        assert len(result) == active_count

    # --- hrp=False: only inactive locations ---

    def test_hrp_false_returns_only_inactive_locations(self):
        result = self._call(_MOCK_GROUPS, hrp=False)
        assert all(r['hrp'] is False for r in result)

    def test_hrp_false_excludes_active_locations(self):
        result = self._call(_MOCK_GROUPS, hrp=False)
        names = [r['name'] for r in result]
        assert 'afghanistan' not in names
        assert 'burundi' not in names

    def test_hrp_false_count(self):
        result = self._call(_MOCK_GROUPS, hrp=False)
        inactive_count = sum(1 for g in _MOCK_GROUPS if g['activity_level'] == 'inactive')
        assert len(result) == inactive_count

    # --- result dict shape ---

    def test_result_contains_expected_keys(self):
        result = self._call(_MOCK_GROUPS)
        expected_keys = {'id', 'name', 'display_name', 'package_count', 'hrp'}
        for item in result:
            assert set(item.keys()) == expected_keys

    def test_result_does_not_contain_activity_level_key(self):
        result = self._call(_MOCK_GROUPS)
        for item in result:
            assert 'activity_level' not in item

    # --- edge cases ---

    def test_empty_group_list_returns_empty_list(self):
        result = self._call([])
        assert result == []

    def test_missing_activity_level_treated_as_inactive(self):
        groups = [{'id': '99', 'name': 'unknown', 'display_name': 'Unknown', 'package_count': 0}]
        result = self._call(groups)
        assert result[0]['hrp'] is False

    def test_missing_activity_level_excluded_by_hrp_true(self):
        groups = [{'id': '99', 'name': 'unknown', 'display_name': 'Unknown', 'package_count': 0}]
        result = self._call(groups, hrp=True)
        assert result == []

    def test_missing_activity_level_included_by_hrp_false(self):
        groups = [{'id': '99', 'name': 'unknown', 'display_name': 'Unknown', 'package_count': 0}]
        result = self._call(groups, hrp=False)
        assert len(result) == 1
        assert result[0]['name'] == 'unknown'
        assert result[0]['hrp'] is False
