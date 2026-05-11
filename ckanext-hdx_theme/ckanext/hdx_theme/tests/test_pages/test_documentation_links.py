import ckan.plugins.toolkit as tk

h = tk.h


def test_header_and_footer_documentation_links(app):
    url = h.url_for('hdx_splash.index')
    response = app.get(url)

    assert response.status_code == 200

    assert 'href="https://docs.humdata.org/"' in response.body
    assert '>Documentation<' in response.body
    assert 'aria-label="documentation link"' in response.body

    assert 'href="https://docs.humdata.org/about/hdx-terms-of-service"' in response.body
    assert 'href="https://docs.humdata.org/publish"' in response.body
    assert 'href="https://docs.humdata.org/build"' in response.body
    assert 'href="https://docs.humdata.org/about/data-licenses"' in response.body
