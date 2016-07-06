'''
Created on September 25, 2015

@author: aartimon

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
    "name": "test_dataset_2",
    "notes": "This is a test dataset",
    "title": "Test Dataset 1",
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

    def test_edit_button_appears(self):
        global package
        user = model.User.by_name('tester')
        testsysadmin = model.User.by_name('testsysadmin')

        dataset_name = package['name']
        context = {'model': model, 'session': model.Session, 'user': 'testsysadmin'}

        self._get_action('organization_create')(context, organization)
        context['user'] = 'tester'

        self._get_action('package_create')(context, package)
        # test that anonymous users can't see the button
        page = self._getPackagePage(dataset_name)
        assert not 'Edit' in str(page.response), 'Anonymous users should not see the edit button'
        # test sysadmin can see edit
        page = self._getPackagePage(dataset_name, testsysadmin.apikey)
        assert 'Edit' in str(page.response), 'Sysadmin''s should see the edit button'
        # test owner can see edit
        page = self._getPackagePage(dataset_name, user.apikey)
        assert 'Edit' in str(page.response), 'Owner should see the edit button'

    def _getPackagePage(self, package_id, apikey=None):
        page = None
        url = h.url_for(controller='package', action='read', id=package_id)
        if apikey:
            page = self.app.get(url, headers={
                'Authorization': unicodedata.normalize('NFKD', apikey).encode('ascii', 'ignore')})
        else:
            page = self.app.get(url)
        return page
