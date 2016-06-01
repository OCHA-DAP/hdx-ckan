import mock
import json
import routes.util as routes_util

import ckan.model as model
import ckan.plugins.toolkit as tk

import ckanext.hdx_theme.tests.hdx_test_base as hdx_test_base
import ckanext.hdx_package.controllers.contribute_flow_controller as contribute_flow_controller
import ckanext.hdx_package.helpers.caching as caching

original_request_config = routes_util.request_config


class TestContributeFlowController(hdx_test_base.HdxBaseTest):

    @classmethod
    def _load_plugins(cls):
        hdx_test_base.load_plugin('hdx_org_group hdx_package hdx_theme')

    @classmethod
    def _create_test_data(cls):

        # we need to invalidate the group caches, otherwise we get data from other tests
        caching.invalidate_group_caches()

        super(TestContributeFlowController, cls)._create_test_data()

        def wrapped_request_config(original=False):
            result = original_request_config(original)
            result.__setattr__('host', 'test.ckan.org')
            result.__setattr__('protocol', 'http')
            return result

        routes_util.request_config = wrapped_request_config

        c = {'ignore_auth': True,
             'model': model, 'session': model.Session, 'user': 'testsysadmin'}

        organization = {
            'name': 'hdx-test-org',
            'title': 'Hdx Test Org',
            'org_url': 'http://test-org.test',
            'description': 'This is a test organization',
            'users': [{'name': 'testsysadmin'}, {'name': 'janedoe3'}]
        }

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
            "groups": [{"name": "roger"}],
            "owner_org": "hdx-test-org"
        }

        resource = {
            'package_id': 'test_contribute_ds',
            'url': 'hdx_contribute_test.csv',
            'resource_type': 'file.upload',
            'url_type': 'upload',
            'format': 'CSV',
            'name': 'hdx_contribute_test.csv'
        }

        tk.get_action('organization_create')(c, organization)
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
    def test_edit_resource_link(self, controller_c_mock, req_mock):

        controller_c_mock.user = 'testsysadmin'
        req_mock.POST = {}

        contribute_flow_controller = MockedContributeFlowController()
        contribute_flow_controller.edit('test_contribute_ds')

        assert contribute_flow_controller.data.get('resources')

        res = contribute_flow_controller.data.get('resources')[0]

        assert res.get('url') == 'hdx_contribute_test.csv', \
            'The dataset is loaded for editing so the uploaded resource "url" field should NOT be the full URL'

        dataset = tk.get_action('package_show')({'model': model, 'session': model.Session},
                                                {'id': 'test_contribute_ds'})

        assert dataset.get('resources')
        assert 'http://test.ckan.org' in dataset.get('resources')[0].get('url', ''), \
            'The dataset is loaded normally so the uploaded resource "url" field should BE the full URL'

    @staticmethod
    def _get_dataset_post_param(dataset_name):

        return {
            'private': 'false',
            'title': dataset_name,
            'name': dataset_name,
            'notes': 'Testing dataset validation',
            'subnational': 1,
            'dataset_source': 'some_source',
            'owner_org': 'hdx-test-org',
            'locations': model.Group.get('roger').id,
            'maintainer': 'testsysadmin',
            'license_id': 'cc-by',
            'methodology': 'Census',
            'data_update_frequency': 0,
            'resources__0__position': 0,
            'resources__0__url': 'http://yahoo.com',
            'resources__0__format': 'link',
            'resources__0__description': '',
            # 'resources__0__originalHash': 97196323,
            'resources__0__url_type': 'api',
            'resources__0__resource_type': 'api',
            'resources__0__name': 'yahoo'
        }

    def test_validate(self):
        user = model.User.by_name('testsysadmin')
        user.email = 'test@test.com'
        auth = {'Authorization': str(user.apikey)}

        post_params = self._get_dataset_post_param('testing-dataset-validation')
        post_params['save'] = 'validate-json'

        res = self.app.post('/contribute/validate', params=post_params,
                            extra_environ=auth)

        json_result = json.loads(res.body)

        assert json_result and len(
            json_result.get('error_summary', [])) == 1, 'There should be only one validation error, date missing'

        post_params["dataset_date"] = "01/01/1960-12/31/2012"

        res2 = self.app.post('/contribute/validate', params=post_params,
                            extra_environ=auth)

        json_result2 = json.loads(res2.body)
        assert json_result2 and not json_result2.get('error_summary'), 'There should be no validation error'

    def test_save(self):
        type(self).use_package_create_wrapper = False
        user = model.User.by_name('testsysadmin')
        user.email = 'test@test.com'
        auth = {'Authorization': str(user.apikey)}

        post_params = self._get_dataset_post_param('testing-dataset-save')
        post_params['save'] = 'new-dataset-json'

        res = self.app.post('/contribute/new', params=post_params,
                            extra_environ=auth)

        json_result = json.loads(res.body)

        assert json_result and len(
            json_result.get('error_summary', [])) == 1, 'There should be only one validation error, date missing'

        post_params["dataset_date"] = "01/01/1960-12/31/2012"

        res2 = self.app.post('/contribute/new', params=post_params,
                             extra_environ=auth)

        json_result2 = json.loads(res2.body)
        assert json_result2 and not json_result2.get('error_summary'), 'There should be no validation error'

        saved_dataset = tk.get_action('package_show')({'model': model}, {'id': 'testing-dataset-save'})

        assert saved_dataset and saved_dataset.get('dataset_date') == "01/01/1960-12/31/2012"

        type(self).use_package_create_wrapper = True

    def test_edit(self):
        type(self).use_package_create_wrapper = False
        user = model.User.by_name('testsysadmin')
        user.email = 'test@test.com'
        auth = {'Authorization': str(user.apikey)}

        post_params = self._get_dataset_post_param('testing-dataset-edit')
        post_params['save'] = 'update-dataset-json'

        post_params["dataset_date"] = "01/01/1960-12/31/2012"

        res = self.app.post('/contribute/new', params=post_params,
                             extra_environ=auth)

        json_result = json.loads(res.body)
        assert json_result and not json_result.get('error_summary'), 'There should be no validation error'

        saved_dataset = tk.get_action('package_show')({'model': model}, {'id': 'testing-dataset-edit'})

        assert saved_dataset and saved_dataset.get('dataset_date') == "01/01/1960-12/31/2012"
        assert saved_dataset.get('id')

        post_params['id'] = saved_dataset.get('id')
        post_params["dataset_date"] = "09/17/2016"

        res2 = self.app.post('/contribute/edit/{}'.format(post_params.get('id')), params=post_params,
                            extra_environ=auth)

        json_result2 = json.loads(res2.body)
        assert json_result2 and not json_result2.get('error_summary'), 'There should be no validation error'

        saved_dataset2 = tk.get_action('package_show')({'model': model}, {'id': 'testing-dataset-edit'})

        assert saved_dataset2 and saved_dataset2.get('dataset_date') == "09/17/2016"

        type(self).use_package_create_wrapper = True


class MockedContributeFlowController(contribute_flow_controller.ContributeFlowController):

    def _prepare_and_render(self, save_type='', data=None, errors=None, error_summary=None):
        self.save_type = save_type
        self.data = data
        self.errors = errors
        self.error_summary = error_summary
