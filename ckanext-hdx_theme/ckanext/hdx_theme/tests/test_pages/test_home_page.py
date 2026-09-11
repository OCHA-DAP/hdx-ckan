from unittest import mock

import ckan.plugins.toolkit as tk
import ckanext.hdx_theme.tests.mock_helper as mh

h = tk.h


class TestHomePage(object):

    @mock.patch('ckanext.hdx_theme.views.splash_page.cached_last_three_signal_cards',
                return_value=mh.mock_signal_cards())
    def test_homepage_signals_section(self, mock_cards, app):
        url = h.url_for('hdx_splash.index')
        response = app.get(url)

        assert response.status_code == 200
        assert 'c-signal-card' in response.body
        assert 'hdx-v2-signal-slide' in response.body
        assert 'hdx-v2-signals-dots' in response.body

    @mock.patch('ckanext.hdx_theme.views.splash_page.cached_last_three_signal_cards',
                side_effect=Exception('Signals CSV unavailable'))
    def test_homepage_signals_section_omitted_on_fetch_failure(self, mock_cards, app):
        url = h.url_for('hdx_splash.index')
        response = app.get(url)

        assert response.status_code == 200
        assert 'c-signal-card' not in response.body
        assert 'hdx-v2-signal-slide' not in response.body
        assert 'hdx-v2-signals-dots' not in response.body
