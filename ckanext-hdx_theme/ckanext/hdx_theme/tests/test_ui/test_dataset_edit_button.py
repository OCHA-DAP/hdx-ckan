'''
Created on September 25, 2015

@author: aartimon

'''
import unicodedata

import ckan.plugins.toolkit as tk
import ckan.lib.helpers as h
import ckan.model as model
import ckan.tests.factories as factories

import ckanext.hdx_users.model as umodel
import ckanext.hdx_user_extra.model as ue_model

import ckanext.hdx_theme.tests.hdx_test_base as hdx_test_base

from ckanext.hdx_org_group.helpers.static_lists import ORGANIZATION_TYPE_LIST

package = {
    "package_creator": "test function",
    "private": False,
    "dataset_date": "[1960-01-01 TO 2012-12-31]",
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
    'hdx_org_type': ORGANIZATION_TYPE_LIST[0][1],
    'org_acronym': 'HTO',
    'org_url': 'https://test-org.test',
    'description': 'This is a test organization',
    'users': [{'name': 'testsysadmin'}, {'name': 'joeadmin', 'capacity': 'member'},
              {'name': 'tester', 'capacity': 'editor'}]
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
        cls.USERS_USED_IN_TEST.append('joeadmin')
        super(TestDatasetOutput, cls).setup_class()
        umodel.setup()
        ue_model.create_table()

    def test_edit_button_appears(self):
        global package
        testsysadmin_token = factories.APIToken(user='testsysadmin', expires_in=2, unit=60 * 60)['token']
        user_token = factories.APIToken(user='tester', expires_in=2, unit=60 * 60)['token']

        dataset_name = package['name']
        context = {'model': model, 'session': model.Session, 'user': 'tester'}
        context_sysadmin = {'model': model, 'session': model.Session, 'user': 'testsysadmin'}

        org_obj = self._get_action('organization_create')(context_sysadmin, organization)

        self._get_action('package_create')(context, package)
        # test that anonymous users can't see the button
        page = self._getPackagePage(dataset_name)
        assert not 'Edit Dataset' in page.body, 'Anonymous users should not see the edit button'
        # test sysadmin can see edit
        page = self._getPackagePage(dataset_name, testsysadmin_token)
        assert 'Edit Dataset' in page.body, 'Sysadmin''s should see the edit button'
        # test owner can see edit
        page = self._getPackagePage(dataset_name, user_token)
        assert 'Edit Dataset' in page.body, 'Owner should see the edit button'

        # test member can NOT see the button
        context['user'] = 'joeadmin'
        member_token = factories.APIToken(user='joeadmin', expires_in=2, unit=60 * 60)['token']
        page = self._getPackagePage(dataset_name, member_token)
        assert 'Edit Dataset' not in page.body, 'Member should NOT see the edit button'

        self._get_action('organization_member_create')(context_sysadmin,
                                                       {'id': org_obj.get('id'), 'username': 'joeadmin',
                                                        'role': 'editor'})
        page = self._getPackagePage(dataset_name, user_token)
        assert 'Edit Dataset' in page.body, 'Editor should see the edit button'

    def _getPackagePage(self, package_id, apitoken=None):
        page = None
        url = h.url_for('dataset_read', id=package_id)
        if apitoken:
            page = self.app.get(url, headers={
                'Authorization': unicodedata.normalize('NFKD', apitoken).encode('ascii', 'ignore')})
        else:
            page = self.app.get(url)
        return page
