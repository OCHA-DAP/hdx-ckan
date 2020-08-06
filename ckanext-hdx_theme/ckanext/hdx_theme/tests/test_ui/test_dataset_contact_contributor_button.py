'''
Created on September 25, 2015

@author: aartimon

'''

import ckan.plugins.toolkit as tk
import ckan.lib.helpers as h
import ckan.model as model
import ckan.lib.create_test_data as ctd
import unicodedata

import ckanext.hdx_users.model as umodel
import ckanext.hdx_user_extra.model as ue_model

import ckanext.hdx_theme.tests.hdx_test_base as hdx_test_base

from ckanext.hdx_org_group.helpers.static_lists import ORGANIZATION_TYPE_LIST

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
    'hdx_org_type': ORGANIZATION_TYPE_LIST[0][1],
    'org_acronym': 'HTO',
    'org_url': 'http://test-org.test',
    'description': 'This is a test organization',
    'users': [{'name': 'joeadmin', 'capacity': 'admin'},
              {'name': 'tester', 'capacity': 'editor'},
              {'name': 'annafan', 'capacity': 'member'}]
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

    def test_contact_contributor_button_appears(self):
        '''
        testsysadmin - sysadmin
        annafan - member
        tester - editor
        joeadmin - admin
        bob - user which is not member of the org

        Any logged in user should see the button

        :return:
        '''

        global package

        user_bob = ctd.CreateTestData.create_user('bob')

        user = model.User.by_name('annafan')
        testsysadmin = model.User.by_name('testsysadmin')

        dataset_name = package['name']
        context = {'model': model, 'session': model.Session, 'user': 'tester'}
        context_sysadmin = {'model': model, 'session': model.Session, 'user': 'testsysadmin'}

        org_obj = self._get_action('organization_create')(context_sysadmin, organization)
        self._get_action('package_create')(context, package)

        # test that anonymous users can't see the button
        page = self._getPackagePage(dataset_name)
        assert '/contact_hdx' in str(page.response), 'Anonymous users should see the contact_hdx link'

        # test sysadmin can see the button
        page = self._getPackagePage(dataset_name, testsysadmin.apikey)
        assert 'contact-the-contributor' in str(page.response), 'Sysadmin users should see contact contributor button'

        # test member/owner can see the button
        page = self._getPackagePage(dataset_name, user.apikey)
        assert 'contact-the-contributor' in str(
            page.response), 'Member/owner should see the  contact contributor button'

        # test editor can see the button
        context['user'] = 'tester'
        user = model.User.by_name('tester')
        page = self._getPackagePage(dataset_name, user.apikey)
        assert 'contact-the-contributor' in str(page.response), 'Editor should see the  contact contributor button'

        # test admin can see the button
        context['user'] = 'joeadmin'
        user = model.User.by_name('joeadmin')
        page = self._getPackagePage(dataset_name, user.apikey)
        assert 'contact-the-contributor' in str(page.response), 'Admin should see the  contact contributor button'


        # any logged in user and not member of organization can NOT see the button
        context['user'] = 'bob'
        page = self._getPackagePage(dataset_name, user_bob.apikey)
        assert 'contact-the-contributor' in str(
            page.response), 'Any loggedin user & not member should NOT see the edit button'


        # self._get_action('organization_member_create')(context_sysadmin,
        #                                                {'id': org_obj.get('id'), 'username': 'joeadmin',
        #                                                 'role': 'editor'})
        # page = self._getPackagePage(dataset_name, user.apikey)
        # assert 'Edit Dataset' in str(page.response), 'Editor should see the edit button'

    def _getPackagePage(self, package_id, apikey=None):
        page = None
        url = h.url_for(controller='package', action='read', id=package_id)
        if apikey:
            page = self.app.get(url, headers={
                'Authorization': unicodedata.normalize('NFKD', apikey).encode('ascii', 'ignore')})
        else:
            page = self.app.get(url)
        return page