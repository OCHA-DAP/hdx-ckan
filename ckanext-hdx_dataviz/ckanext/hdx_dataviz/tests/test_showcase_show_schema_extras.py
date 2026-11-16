"""
Regression tests for showcase indexing and showcase show by non-sysadmin users.

CKAN 2.11.7 changed default_extras_schema so that the extras 'id' runs
ignore_not_sysadmin first. The showcase show schema keeps that extras schema and
also uses convert_from_extras (image_url and the dataviz fields), which removes the
extras entry before its 'id' is checked, so validation without a sysadmin user
crashed with KeyError: ('extras', 0, 'id').
The search index validates with no user, so showcases were silently not indexed
(core logs and swallows the error), and package_show without the index cache
returned a 500 for non-sysadmins.
See fix_show_schema_extras_id in ckanext-hdx_theme/ckanext/hdx_theme/util/schema.py.
"""

import json

import pytest

import ckan.lib.search as search
import ckan.model as model
import ckan.plugins.toolkit as tk
from ckan.types import Context

from ckanext.hdx_dataviz.tests import USER, SYSADMIN

_get_action = tk.get_action

SHOWCASE_NAME = 'hdx-test-showcase-extras'
IMAGE_URL = 'https://hdx.hdxtest.org/showcase.png'
# an extra that the show schema does not convert to a top-level field, so it stays
# in 'extras' with its 'id' (covers the case where the id is present)
UNMAPPED_EXTRA_KEY = 'hdx_test_unmapped_extra'
ANONYMOUS = ''


def _context(user: str) -> Context:
    # use_cache False: validate with the caller's user instead of reading the
    # validated_data_dict from the search index
    return {'model': model, 'session': model.Session, 'user': user, 'use_cache': False}


@pytest.fixture()
def showcase_with_extras(setup_user_data):
    context = {'model': model, 'session': model.Session, 'user': SYSADMIN}
    return _get_action('ckanext_showcase_create')(context, {
        'name': SHOWCASE_NAME,
        'title': 'HDX TEST SHOWCASE EXTRAS',
        'notes': 'This is a test showcase',
        'image_url': IMAGE_URL,
        'in_dataviz_gallery': True,
        'dataviz_label': 'Test Label',
        'extras': [{'key': UNMAPPED_EXTRA_KEY, 'value': 'kept'}],
    })


@pytest.mark.usefixtures('keep_db_tables_on_clean', 'clean_db', 'clean_index', 'showcase_with_extras')
class TestShowcaseShowSchemaExtras(object):

    def test_showcase_is_indexed(self):
        indexed = search.show(SHOWCASE_NAME)

        validated = json.loads(indexed['validated_data_dict'])
        assert validated['image_url'] == IMAGE_URL
        assert validated['in_dataviz_gallery'] is True

    @pytest.mark.parametrize('user', [ANONYMOUS, USER, SYSADMIN])
    def test_showcase_show(self, user):
        showcase_dict = _get_action('ckanext_showcase_show')(_context(user), {'id': SHOWCASE_NAME})

        assert showcase_dict['image_url'] == IMAGE_URL
        assert showcase_dict['in_dataviz_gallery'] is True
        assert showcase_dict['dataviz_label'] == 'Test Label'

        unmapped = [e for e in showcase_dict['extras'] if e['key'] == UNMAPPED_EXTRA_KEY]
        assert len(unmapped) == 1
        assert unmapped[0]['value'] == 'kept'
        # core rule (ignore_not_sysadmin): only sysadmins get the extras id back
        assert ('id' in unmapped[0]) == (user == SYSADMIN)
