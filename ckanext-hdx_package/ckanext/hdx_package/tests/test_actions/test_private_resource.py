'''
Created on Nov 10, 2014

@author: alexandru-m-g
'''

import logging as logging
import pylons.config as config

import ckan.plugins.toolkit as tk
import ckan.model as model
import ckan.lib.helpers as h
import ckan.tests as tests

import ckanext.hdx_theme.tests.hdx_test_base as hdx_test_base

log = logging.getLogger(__name__)


organization = {'name': 'hdx-test-org',
                'title': 'Hdx Test Org', 'users': [{'name': 'testsysadmin'}]}


package = {
    "package_creator": "test function",
    "private": True,
    "dataset_date": "01/01/1960-12/31/2012",
    "indicator": "1",
    "caveats": "These are the caveats",
    "license_other": "TEST OTHER LICENSE",
    "methodology": "This is a test methodology",
    "dataset_source": "World Bank",
    "license_id": "hdx-other",
    "name": "test_activity_1",
    "notes": "This is a test activity",
    "title": "Test Activity 1",
    "indicator": 1,
    "groups": [{"name": "roger"}],
    "owner_org": "hdx-test-org",
}

resource = {
    'package_id': 'test_activity_1',
    'url': config.get('ckan.site_url', '') + '/storage/f/test_folder/hdx_test.csv',
    'resource_type': 'file.upload',
    'format': 'CSV',
    'name': 'hdx_test.csv'
}

log = logging.getLogger(__name__)


class TestHDXPrivateResource(hdx_test_base.HdxBaseTest):

    @classmethod
    def _load_plugins(cls):
        hdx_test_base.load_plugin('hdx_package hdx_theme')

    @classmethod
    def _get_action(cls, action_name):
        return tk.get_action(action_name)

    def test_hdx_access_to_private_resource(self):
        global package, resource, organization

        config['ofs.impl'] = 'pairtree'
        config['ofs.storage_dir'] = '/tmp'

        testsysadmin = model.User.by_name('testsysadmin')
        tester = model.User.by_name('tester')

        context = {
            'model': model, 'session': model.Session, 'user': 'testsysadmin'}

        self._get_action('organization_create')(context, organization)

        orgs = self._get_action('organization_list')(context, {})

        self._get_action('package_create')(context, package)
        # This is a copy of the hack done in dataset_controller
        self._get_action('package_update')(context, package)

        self._get_action('resource_create')(context, resource)

        resource = self._get_action('resource_show')(
            context, {'id': 'hdx_test.csv'})

        dwld_url = h.url_for(controller='ckanext.hdx_package.controllers.storage_controller:FileDownloadController',
                             action='file', label='test_folder/hdx_test.csv')

        # Testing access to private resource
        try:
            self.app.get(
                dwld_url,
                extra_environ={'Authorization': str(testsysadmin.apikey)})
        except Exception, e:
            # The file doesn't really exist
            assert '404' in e.args[0], 'File not found'
        try:
            self.app.get(
                dwld_url, extra_environ={'Authorization': str(tester.apikey)})
        except Exception, e:
            assert '403' in e.args[0], 'Not Authorized for other user'
        try:
            self.app.get(dwld_url)
        except Exception, e:
            assert '403' in e.args[0], 'Not Authorized for guest'

        # Testing access to the private dataset
        tests.call_action_api(self.app, 'package_show', id='test_activity_1',
                              status=403)
        tests.call_action_api(self.app, 'package_show', id='test_activity_1',
                              apikey=tester.apikey, status=403)
        tests.call_action_api(self.app, 'package_show', id='test_activity_1',
                              apikey=testsysadmin.apikey, status=200)
