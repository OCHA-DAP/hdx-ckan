import pytest
import os

import ckan.plugins.toolkit as tk
import ckan.model as model
import ckan.tests.factories as factories

_get_action = tk.get_action
config_path = os.path.join(os.path.dirname(__file__), "test_config.json")
config = tk.config


@pytest.mark.usefixtures("clean_db")
@pytest.mark.ckan_config("hdx.checks.config_path", config_path)
@pytest.mark.ckan_config("hdx_test.url_for_passing_check", "https://google.com")
class TestServiceCheckerApi(object):

    def test_run_checks(self):
        user = factories.User(name='test_sysadmin_service_checker_user1', sysadmin=True)
        context = {
            'model': model,
            'user': user['name']
        }
        result = _get_action('run_checks')(context, {})
        dummy_result = result[0]
        assert dummy_result['type'] == 'Dummy Check'
        assert dummy_result['error_message'] == 'Dummy message'
        assert dummy_result['result'] == 'Passed'

        failed_result = result[1]
        assert failed_result['type'] == 'Dummy Check'
        assert 'hdx_test.var_that_cant_be_found' in failed_result['error_message']
        assert failed_result['result'] == 'Failed'

        passed_result = result[2]
        assert passed_result['type'] == 'HTTP Response Text Check'
        assert not passed_result['error_message']
        assert passed_result['result'] == 'Passed'
