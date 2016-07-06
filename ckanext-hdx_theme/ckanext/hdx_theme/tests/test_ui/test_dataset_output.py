'''
Created on May 16, 2014

@author: alexandru-m-g

'''

import ckan.tests as tests
import ckan.plugins.toolkit as tk
import ckan.lib.helpers as h
import ckan.model as model
import unicodedata

import ckanext.hdx_users.model as umodel
import ckanext.hdx_user_extra.model as ue_model

import ckanext.hdx_theme.tests.hdx_test_base as hdx_test_base

package = {
    "package_creator": "test function",
    "private": False,
    "dataset_date": "01/01/1960-12/31/2012",
    "indicator": "1",
    "caveats": "These are the caveats",
    "license_other": "TEST OTHER LICENSE",
    "methodology": "This is a test methodology",
    "dataset_source": "World Bank",
    "license_id": "hdx-other",
    "name": "test_dataset_1",
    "notes": "This is a test dataset",
    "title": "Test Dataset 1",
    "indicator": 1,
    "owner_org": "hdx-test-org",
    "groups": [{"name": "roger"}]
}

organization = {
    'name': 'hdx-test-org',
    'title': 'Hdx Test Org',
    'org_url': 'http://test-org.test',
    'description': 'This is a test organization',
    'users': [{'name': 'testsysadmin'}, {'name': 'janedoe3'}]
}


class TestDatasetOutput(hdx_test_base.HdxBaseTest):
    # loads missing plugins
    @classmethod
    def _load_plugins(cls):
        hdx_test_base.load_plugin('hdx_org_group hdx_package hdx_users hdx_user_extra hdx_theme')

    @classmethod
    def _get_action(cls, action_name):
        return tk.get_action(action_name)

    @classmethod
    def setup_class(cls):
        super(TestDatasetOutput, cls).setup_class()
        umodel.setup()
        ue_model.create_table()

    def test_deleted_badge_appears(self):
        global package
        global organization
        testsysadmin = model.User.by_name('testsysadmin')
        dataset_name = package['name']
        context = {'model': model, 'session': model.Session, 'user': 'testsysadmin'}

        tk.get_action('organization_create')(context, organization)

        self._get_action('package_create')(context, package)

        page = self._getPackagePage(dataset_name)
        assert not 'Deleted' in str(page.response), 'Page should not have deleted badge as it was not deleted'

        deleted_result = tests.call_action_api(self.app, 'package_delete',
                                               apikey=testsysadmin.apikey, id=dataset_name)

        deleted_page = self._getPackagePage(dataset_name, testsysadmin.apikey)
        # print deleted_page.response
        assert 'Deleted' in str(deleted_page.response), 'Page needs to have deleted badge'

    def _getPackagePage(self, package_id, apikey=None):
        page = None
        url = h.url_for(controller='package', action='read', id=package_id)
        if apikey:
            page = self.app.get(url, headers={
                'Authorization': unicodedata.normalize('NFKD', apikey).encode('ascii', 'ignore')})
        else:
            page = self.app.get(url)
        return page
