import pytest

import ckan.plugins.toolkit as tk
import ckan.tests.factories as factories
from ckanext.hdx_dataviz.tests import generate_test_showcase, USER, SYSADMIN, ORG, LOCATION

_url_for = tk.url_for


@pytest.mark.usefixtures('keep_db_tables_on_clean', 'hdx_clean_db', 'clean_index', 'setup_user_data')
def test_dataviz_page_load(app):
    sysadmin_token = factories.APIToken(user=SYSADMIN, expires_in=2, unit=60 * 60)['token']
    generate_test_showcase(SYSADMIN, 'dataviz-gallery-1', True)
    generate_test_showcase(SYSADMIN, 'dataviz-gallery-2', True)
    url = _url_for('hdx_dataviz_gallery.index')
    response = app.get(url)
    assert response.status_code == 200
    assert 'dataviz-gallery-1' in response.body
    assert 'dataviz-gallery-2' in response.body
    assert 'Edit' not in response.body

    response2 = app.get(url, headers={'Authorization': sysadmin_token})

    assert 'Edit' in response2.body
