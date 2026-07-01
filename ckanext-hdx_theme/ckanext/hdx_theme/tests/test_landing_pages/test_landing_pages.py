import pytest

import ckan.plugins.toolkit as tk
import ckan.tests.factories as factories

h = tk.h
ValidationError = tk.ValidationError


class TestLandingPages(object):
    username = 'test_sysadmin_landing_pages_user'
    api_token = None

    def test_hapi_landing_page_without_auth(self, app):
        url = h.url_for('hdx_landing_pages.hapi')
        response = app.get(url)

        assert response.status_code == 200
        assert "'pageTitle': 'HDX HAPI Beta'" in response.body
        assert "'authenticated': 'false'" in response.body

        assert 'src="/visualization/hapi-availability/"' in response.body

        assert '<h2 class="hdx-v2-hapi-section-heading">FAQ</h2>' in response.body
        assert 'c-accordion__trigger' in response.body
        assert 'c-accordion__body' in response.body

        assert '<h2 class="hdx-v2-hapi-section-heading">Partners</h2>' in response.body
        assert 'landing_pages/partners' in response.body

    def test_signals_landing_page_without_auth(self, app):
        url = h.url_for('hdx_landing_pages.signals')
        response = app.get(url)

        assert response.status_code == 200
        assert "'pageTitle': 'HDX Signals'" in response.body
        assert "'authenticated': 'false'" in response.body

        assert 'id="mc-embedded-subscribe-form" name="mc-embedded-subscribe-form"' in response.body

        assert '<h2 class="hdx-v2-signals-section-heading">Data Coverage</h2>' in response.body

        assert '<h2 class="hdx-v2-signals-section-heading">Resources</h2>' in response.body

        assert '<h2 class="hdx-v2-signals-section-heading">FAQs</h2>' in response.body
        assert 'c-accordion__trigger' in response.body
        assert 'c-accordion__body' in response.body

        assert '<h2 class="hdx-v2-signals-section-heading">Partners</h2>' in response.body
        assert 'landing_pages/partners' in response.body

    @pytest.mark.usefixtures("hdx_clean_db")
    def test_hapi_landing_page_with_auth(self, app):
        factories.User(name=self.username, sysadmin=True)
        api_token = factories.APIToken(user=self.username, expires_in=2, unit=60 * 60)['token']
        auth = {"Authorization": api_token}
        url = h.url_for('hdx_landing_pages.hapi')
        response = app.get(url, headers=auth)

        assert response.status_code == 200
        assert "'pageTitle': 'HDX HAPI Beta'" in response.body
        assert "'authenticated': 'true'" in response.body

    @pytest.mark.usefixtures("hdx_clean_db")
    def test_signals_landing_page_with_auth(self, app):
        factories.User(name=self.username, sysadmin=True)
        api_token = factories.APIToken(user=self.username, expires_in=2, unit=60 * 60)['token']
        auth = {"Authorization": api_token}
        url = h.url_for('hdx_landing_pages.signals')
        response = app.get(url, headers=auth)

        assert response.status_code == 200
        assert "'pageTitle': 'HDX Signals'" in response.body
        assert "'authenticated': 'true'" in response.body
