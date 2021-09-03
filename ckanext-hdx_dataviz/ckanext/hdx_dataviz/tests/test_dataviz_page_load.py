import pytest
import six

import ckan.plugins.toolkit as tk

from ckanext.hdx_dataviz.tests import generate_test_showcase, USER, SYSADMIN, ORG, LOCATION

_url_for = tk.url_for


@pytest.mark.skipif(six.PY3, reason=u"The user_extras plugin is not available on PY3 yet")
@pytest.mark.usefixtures('keep_db_tables_on_clean', 'clean_db', 'clean_index', 'setup_user_data')
def test_dataviz_page_load(app):
    generate_test_showcase(SYSADMIN, 'dataviz-gallery-1', True)
    generate_test_showcase(SYSADMIN, 'dataviz-gallery-2', True)
    url = _url_for('hdx_dataviz_gallery.index')
    response = app.get(url)
    assert response.status_code == 200
    assert 'dataviz-gallery-1' in response.body
    assert 'dataviz-gallery-2' in response.body
    assert 'Edit Showcase' not in response.body

    response2 = app.get(url, environ_overrides={"REMOTE_USER": SYSADMIN})
    assert 'Edit Showcase' in response2.body
