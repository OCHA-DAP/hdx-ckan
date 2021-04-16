import pytest

import ckan.model as model
import ckan.plugins.toolkit as tk
import ckan.tests.factories as factories

from ckanext.hdx_service_checker.tests.test_api import config_path

h = tk.h


@pytest.mark.ckan_config("hdx.checks.config_path", config_path)
@pytest.mark.usefixtures("with_request_context")
@pytest.mark.ckan_config("hdx_test.url_for_passing_check", "https://google.com")
class TestServiceCheckerController(object):
    username = 'test_sysadmin_service_checker_user2'
    apikey = username + '_apikey'

    @classmethod
    @pytest.mark.usefixtures("clean_db")
    def setup_class(cls):
        factories.User(name=cls.username, sysadmin=True)
        user = model.User.by_name(cls.username)
        user.apikey = cls.apikey
        model.Session.commit()

    def test_run_checks(self, app):
        auth = {"Authorization": str(self.apikey)}
        url = h.url_for('hdx_run_checks.run_checks')
        response = app.get(url)
        assert response.status_code == 403
        response = app.get(url, headers=auth)
        assert response.status_code == 200
        assert 'Dummy check -- Passed' in response.body
        assert 'Failing check -- Failed' in response.body
        assert 'Passing check -- Passed' in response.body

