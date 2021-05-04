import pytest

import ckan.model as model
import ckan.plugins.toolkit as tk
import ckan.tests.factories as factories

h = tk.h
ValidationError = tk.ValidationError


@pytest.mark.usefixtures("with_request_context")
class TestServiceCheckerController(object):
    username = 'test_sysadmin_colored_pages_user2'
    apikey = username + '_apikey'

    title = 'test_title'
    color = 'AB00BA'

    def test_render_without_auth(self, app):
        url = h.url_for('hdx_colored_page.read', category='test_category', title=self.title)
        response = app.get(url)
        assert response.status_code == 200
        assert "'pageTitle': '{}'".format(self.title) in response.body
        assert "'authenticated': 'false'" in response.body
        assert 'background-color: #fff' in response.body, '#fff is the default color'

        url = h.url_for('hdx_colored_page.read', category='test_category', title=self.title, color=self.color)
        response = app.get(url)
        assert response.status_code == 200
        assert "'pageTitle': '{}'".format(self.title) in response.body
        assert "'authenticated': 'false'" in response.body
        assert 'background-color: #{}'.format(self.color) in response.body

    @pytest.mark.usefixtures("clean_db")
    def test_render_with_auth(self, app):
        factories.User(name=self.username, sysadmin=True)
        user = model.User.by_name(self.username)
        user.apikey = self.apikey
        model.Session.commit()

        auth = {"Authorization": str(self.apikey)}
        url = h.url_for('hdx_colored_page.read', category='test_category', title=self.title, color=self.color)
        response = app.get(url, headers=auth)
        assert response.status_code == 200
        assert "'pageTitle': '{}'".format(self.title) in response.body
        assert "'authenticated': 'true'" in response.body
        assert 'background-color: #{}'.format(self.color) in response.body

    def test_render_with_bad_color(self, app):
        url = h.url_for('hdx_colored_page.read', category='test_category', title=self.title, color='xyz')
        response = app.get(url)
        assert response.status_code == 500

        url = h.url_for('hdx_colored_page.read', category='test_category', title=self.title, color='1234567')
        response = app.get(url)
        assert response.status_code == 500


