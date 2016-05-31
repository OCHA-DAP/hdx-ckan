import routes.util as routes_util
import mock

import ckan.model as model
import ckan.plugins.toolkit as tk

import ckanext.hdx_theme.tests.hdx_test_base as hdx_test_base
import ckanext.hdx_package.controllers.contribute_flow_controller as contribute_flow_controller

original_request_config = routes_util.request_config


class TestContributeFlowController(hdx_test_base.HdxBaseTest):

    @classmethod
    def _load_plugins(cls):
        hdx_test_base.load_plugin('hdx_package hdx_theme')

    @classmethod
    def _create_test_data(cls):
        super(TestContributeFlowController, cls)._create_test_data()

        def wrapped_request_config(original=False):
            result = original_request_config(original)
            result.__setattr__('host', 'test.ckan.org')
            result.__setattr__('protocol', 'http')
            return result

        routes_util.request_config = wrapped_request_config

        c = {'ignore_auth': True,
             'model': model, 'session': model.Session, 'user': 'testsysadmin'}

        package = {
            "package_creator": "testsysadmin",
            "private": False,
            "dataset_date": "01/01/1960-12/31/2012",
            "indicator": "0",
            "caveats": "These are the caveats",
            "license_other": "TEST OTHER LICENSE",
            "methodology": "This is a test methodology",
            "dataset_source": "World Bank",
            "license_id": "hdx-other",
            "name": "test_contribute_ds",
            "notes": "This is a dataset for testing the contribute flow controller",
            "title": "Test Contribute Dataset",
            "groups": [{"name": "roger"}]
        }

        resource = {
            'package_id': 'test_contribute_ds',
            'url': 'hdx_contribute_test.csv',
            'resource_type': 'file.upload',
            'url_type': 'upload',
            'format': 'CSV',
            'name': 'hdx_contribute_test.csv'
        }

        tk.get_action('package_create')(c, package)
        tk.get_action('resource_create')({
            'ignore_auth': True, 'model': model, 'session': model.Session,
            'user': 'testsysadmin', 'return_id_only': True},
            resource)

    @classmethod
    def teardown_class(cls):
        routes_util.request_config = original_request_config
        super(TestContributeFlowController, cls).teardown_class()

    @mock.patch('ckanext.hdx_package.controllers.contribute_flow_controller.request')
    @mock.patch('ckanext.hdx_package.controllers.contribute_flow_controller.c')
    def test_edit(self, controller_c_mock, req_mock):

        controller_c_mock.user = 'testsysadmin'
        req_mock.POST = {}

        contribute_flow_controller = MockedContributeFlowController()
        contribute_flow_controller.edit('test_contribute_ds')

        assert contribute_flow_controller.data.get('resources')

        res = contribute_flow_controller.data.get('resources')[0]

        assert res.get('url') == 'hdx_contribute_test.csv'

        dataset = tk.get_action('package_show')({'model': model, 'session': model.Session}, {'id': 'test_contribute_ds'})

        assert dataset.get('resources')
        assert 'http://test.ckan.org' in dataset.get('resources')[0].get('url', '')


class MockedContributeFlowController(contribute_flow_controller.ContributeFlowController):

    def _prepare_and_render(self, save_type='', data=None, errors=None, error_summary=None):
        self.save_type = save_type
        self.data = data
        self.errors = errors
        self.error_summary = error_summary
