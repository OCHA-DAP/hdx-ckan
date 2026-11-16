"""
Regression tests for group_show / organization_show called by non-sysadmin users.

CKAN 2.11.7 changed default_extras_schema so that the extras 'id' runs
ignore_not_sysadmin first. Our show schemas keep that extras schema and also use
convert_from_extras, which removes the extras entry before its 'id' is checked,
so calls by non-sysadmins crashed with KeyError: ('extras', 0, 'id').
That hid the home page bar chart and returned a 500 on /group.
See _fix_show_schema_extras_id in ckanext/hdx_org_group/plugin.py.
"""

import pytest

import ckan.model as model
import ckan.plugins.toolkit as tk
import ckan.tests.factories as factories
from ckan.types import Context

from ckanext.hdx_org_group.tests.conftest import ORG, USER, SYSADMIN

_get_action = tk.get_action

LOCATION_WITH_EXTRAS = 'hdx-test-location-extras'
# an extra that the show schema does not convert to a top-level field, so it stays
# in 'extras' with its 'id' (covers the case where the id is present)
UNMAPPED_EXTRA_KEY = 'hdx_test_unmapped_extra'
ANONYMOUS = ''


def _context(user: str) -> Context:
    return {'model': model, 'session': model.Session, 'user': user}


@pytest.fixture()
def location_with_extras(hdx_clean_db, setup_user_data):
    factories.Group(
        name=LOCATION_WITH_EXTRAS,
        title='HDX TEST LOCATION EXTRAS',
        activity_level='active',
        language_code='fr',
        extras=[{'key': UNMAPPED_EXTRA_KEY, 'value': 'kept'}],
    )


@pytest.mark.usefixtures('keep_db_tables_on_clean', 'hdx_clean_db', 'clean_index', 'setup_user_data',
                         'location_with_extras')
class TestShowSchemaExtras(object):

    @pytest.mark.parametrize('user', [ANONYMOUS, USER, SYSADMIN])
    def test_group_show(self, user):
        group_dict = _get_action('group_show')(_context(user), {'id': LOCATION_WITH_EXTRAS})

        assert group_dict['activity_level'] == 'active'
        assert group_dict['language_code'] == 'fr'

        unmapped = [e for e in group_dict['extras'] if e['key'] == UNMAPPED_EXTRA_KEY]
        assert len(unmapped) == 1
        assert unmapped[0]['value'] == 'kept'
        # core rule (ignore_not_sysadmin): only sysadmins get the extras id back
        assert ('id' in unmapped[0]) == (user == SYSADMIN)

    @pytest.mark.parametrize('user', [ANONYMOUS, USER, SYSADMIN])
    def test_organization_show(self, user):
        org_dict = _get_action('organization_show')(_context(user), {'id': ORG})

        assert org_dict['hdx_org_type'] == 'donor'

    def test_group_list_like_cached_group_list(self):
        # Same call as ckanext.hdx_package.helpers.caching.cached_group_list,
        # which feeds the home page bar chart and the /group page.
        groups = _get_action('group_list')(_context('127.0.0.1'), {
            'all_fields': True,
            'include_extras': True,
            'package_count': True,
        })

        location = next(g for g in groups if g['name'] == LOCATION_WITH_EXTRAS)
        assert location['activity_level'] == 'active'
