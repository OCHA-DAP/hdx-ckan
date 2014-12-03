'''
Created on Dec 2, 2014

@author: alexandru-m-g
'''

import logging as logging

import ckan.model as model
import ckan.lib.helpers as h

import ckanext.hdx_theme.tests.hdx_test_base as hdx_test_base
import ckanext.hdx_theme.tests.hdx_test_with_inds_and_orgs as hdx_test_with_inds_and_orgs

log = logging.getLogger(__name__)


class TestPermaLinkDisplay(hdx_test_with_inds_and_orgs.HDXWithIndsAndOrgsTest):

    @classmethod
    def _load_plugins(cls):
        hdx_test_base.load_plugin('hdx_package hdx_theme')

    def test_hdx_access_to_private_resource(self):
        testsysadmin = model.User.by_name('testsysadmin')
        context = {
            'model': model, 'session': model.Session, 'user': 'testsysadmin'}
        resource = self._get_action('resource_show')(
            context, {'id': 'hdx_test.csv'})
        perma_link = h.url_for(controller='ckanext.hdx_package.controllers.storage_controller:FileDownloadController',
                               action='perma_file', id='test_private_dataset_1', resource_id=resource['id'])

        test_dataset_url = h.url_for(controller='ckanext.hdx_package.controllers.dataset_controller:DatasetController',
                                     action='read', id='test_private_dataset_1')

        try:
            result = self.app.get(
                test_dataset_url, extra_environ={'Authorization': str(testsysadmin.apikey)})
            assert perma_link in str(result)
        except Exception, e:
            assert False, str(e)
