"""
Unit tests for fix_show_schema_extras_id in ckanext/hdx_theme/util/schema.py.

The behaviour of the fixed schemas (group, organization and showcase show) is
covered by test_show_schema_extras.py in hdx_org_group and
test_showcase_show_schema_extras.py in hdx_dataviz.
"""

import ckan.plugins.toolkit as tk
from ckan.logic.schema import default_extras_schema

from ckanext.hdx_theme.util.schema import fix_show_schema_extras_id


def _core_extras_id():
    return default_extras_schema()['id']


def test_prepends_ignore_missing():
    schema = fix_show_schema_extras_id({'extras': default_extras_schema()})

    assert schema['extras']['id'] == [tk.get_validator('ignore_missing'), *_core_extras_id()]


def test_applying_twice_does_not_prepend_again():
    # the hdx_dataviz showcase wrapper is applied again on every plugin load
    schema = fix_show_schema_extras_id(fix_show_schema_extras_id({'extras': default_extras_schema()}))

    assert schema['extras']['id'] == [tk.get_validator('ignore_missing'), *_core_extras_id()]


def test_show_style_extras_without_id_unchanged():
    keep_extras = tk.get_validator('keep_extras')
    schema = fix_show_schema_extras_id({'extras': {'__extras': [keep_extras]}})

    assert schema == {'extras': {'__extras': [keep_extras]}}


def test_schema_without_extras_unchanged():
    assert fix_show_schema_extras_id({'name': []}) == {'name': []}
