import ckan.plugins.toolkit as tk

from ckanext.hdx_package.helpers.constants import DOCUMENTATION_LINKS


def test_documentation_links_rendered(app):
    url = tk.h.url_for('hdx_splash.index')
    response = app.get(url)

    assert response.status_code == 200

    assert f'href="{DOCUMENTATION_LINKS["MAIN"]}"' in response.body
    assert '>Documentation<' in response.body
    assert 'aria-label="documentation link"' in response.body

    assert f'href="{DOCUMENTATION_LINKS["TERMS_OF_SERVICE"]}"' in response.body
    assert f'href="{DOCUMENTATION_LINKS["QA_PROCESS"]}"' in response.body
    assert f'href="{DOCUMENTATION_LINKS["RESOURCES_FOR_DEVELOPERS"]}"' in response.body
    assert f'href="{DOCUMENTATION_LINKS["DATA_LICENSES"]}"' in response.body
