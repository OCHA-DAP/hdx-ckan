from unittest import mock

import ckan.plugins.toolkit as tk

import ckanext.hdx_theme.tests.mock_helper as mh
from ckanext.hdx_package.helpers.constants import DOCUMENTATION_LINKS


@mock.patch('ckanext.hdx_theme.views.splash_page.cached_last_three_signal_cards',
            return_value=mh.mock_signal_cards())
def test_documentation_links_rendered(mock_cards, app):
    url = tk.h.url_for('hdx_splash.index')
    response = app.get(url)

    assert response.status_code == 200

    # Header documentation link.
    assert f'href="{DOCUMENTATION_LINKS["MAIN"]}"' in response.body
    assert 'Documentation' in response.body
    assert 'aria-label="documentation link"' in response.body

    # Footer documentation links and labels.
    assert f'href="{DOCUMENTATION_LINKS["TERMS_OF_SERVICE"]}"' in response.body
    assert f'href="{DOCUMENTATION_LINKS["QA_PROCESS"]}"' in response.body
    assert f'href="{DOCUMENTATION_LINKS["RESOURCES_FOR_DEVELOPERS"]}"' in response.body
    assert f'href="{DOCUMENTATION_LINKS["DATA_LICENSES"]}"' in response.body
    assert 'Terms of Service' in response.body
    assert 'QA Process' in response.body
    assert 'Build with HDX' in response.body
    assert 'Data Licenses' in response.body
