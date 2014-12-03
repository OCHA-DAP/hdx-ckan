'''
Created on Nov 10, 2014

@author: alexandru-m-g
'''

import logging as logging
import pylons.config as config

import ckan.model as model
import ckan.lib.helpers as h
import ckan.tests as tests

import ckanext.hdx_theme.tests.hdx_test_base as hdx_test_base
import ckanext.hdx_theme.tests.hdx_test_with_inds_and_orgs as hdx_test_with_inds_and_orgs

log = logging.getLogger(__name__)


class TestHDXPrivateResource(hdx_test_with_inds_and_orgs.HDXWithIndsAndOrgsTest):

    @classmethod
    def _load_plugins(cls):
        hdx_test_base.load_plugin('hdx_package hdx_theme')

    def test_hdx_access_to_private_resource(self):

        config['ofs.impl'] = 'pairtree'
        config['ofs.storage_dir'] = '/tmp'

        testsysadmin = model.User.by_name('testsysadmin')
        tester = model.User.by_name('tester')

        context = {
            'model': model, 'session': model.Session, 'user': 'testsysadmin'}

        resource = self._get_action('resource_show')(
            context, {'id': 'hdx_test.csv'})

        dwld_url = h.url_for(controller='ckanext.hdx_package.controllers.storage_controller:FileDownloadController',
                             action='file', label='test_folder/hdx_test.csv')

        # Testing access to private resource on old url
        try:
            self.app.get(
                dwld_url,
                extra_environ={'Authorization': str(testsysadmin.apikey)})
        except Exception, e:
            # The file doesn't really exist
            assert '404' in e.args[0], 'File not found'
        try:
            result = self.app.get(
                dwld_url, extra_environ={'Authorization': str(tester.apikey)})
            assert '403 Access Denied' in str(result)
        except Exception, e:
            assert False
        try:
            result = self.app.get(dwld_url)
            assert '403 Access Denied' in str(result)
        except Exception, e:
            assert False

        perma_link = h.url_for(controller='ckanext.hdx_package.controllers.storage_controller:FileDownloadController',
                               action='perma_file', id='test_private_dataset_1', resource_id=resource['id'])

        # Testing access to private resource on perma_link
        try:
            self.app.get(
                perma_link,
                extra_environ={'Authorization': str(testsysadmin.apikey)})
        except Exception, e:
            # The file doesn't really exist
            assert '404' in e.args[0], 'File not found'
        try:
            result = self.app.get(
                perma_link, extra_environ={'Authorization': str(tester.apikey)})
            assert '403 Access Denied' in str(result)
        except Exception, e:
            assert False
        try:
            result = self.app.get(perma_link)
            assert '403 Access Denied' in str(result)
        except Exception, e:
            assert False

        # Testing access to the private resource API
        tests.call_action_api(self.app, 'resource_show', id=resource['id'],
                              status=403)
        tests.call_action_api(self.app, 'resource_show', id=resource['id'],
                              apikey=tester.apikey, status=403)

        tests.call_action_api(self.app, 'resource_show', id=resource[
                              'id'], apikey=testsysadmin.apikey, status=200)

        # Testing access to the private dataset API
        tests.call_action_api(self.app, 'package_show', id='test_private_dataset_1',
                              status=403)
        tests.call_action_api(self.app, 'package_show', id='test_private_dataset_1',
                              apikey=tester.apikey, status=403)
        tests.call_action_api(self.app, 'package_show', id='test_private_dataset_1',
                              apikey=testsysadmin.apikey, status=200)
