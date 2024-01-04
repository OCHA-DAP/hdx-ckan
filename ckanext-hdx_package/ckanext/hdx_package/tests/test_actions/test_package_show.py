'''
Created on Jun 20, 2018

@author: danmihaila
'''

import logging as logging

import ckan.model as model
import ckan.plugins.toolkit as tk

import ckanext.hdx_theme.tests.hdx_test_with_inds_and_orgs as hdx_test_with_inds_and_orgs

log = logging.getLogger(__name__)


_get_action = tk.get_action

class TestHDXPackageShow(hdx_test_with_inds_and_orgs.HDXWithIndsAndOrgsTest):

    @classmethod
    def setup_class(cls):
        cls.USERS_USED_IN_TEST.append('johndoe1')
        super(TestHDXPackageShow, cls).setup_class()

    @classmethod
    def _create_test_data(cls):
        super(TestHDXPackageShow, cls)._create_test_data(create_datasets=True, create_members=True)

    def test_hdx_access_to_private_resource(self):

        context = {'model': model, 'session': model.Session, 'user': 'testsysadmin'}
        result = _get_action('package_show')(context, {'id': 'test_dataset_1'})
        assert 'maintainer_email' in result

        context = {'model': model, 'session': model.Session, 'user': 'johndoe1'}
        result = _get_action('package_show')(context, {'id': 'test_dataset_1'})
        assert 'maintainer_email' in result

        context = {'model': model, 'session': model.Session}
        result = _get_action('package_show')(context, {'id': 'test_dataset_1'})
        assert 'maintainer_email' not in result

        context = {'model': model, 'session': model.Session, 'user': 'testsysadmin'}
        result = _get_action('package_search')(context, {'q': '*:*', 'fq': 'name:test_dataset_1'})
        for dataset in result['results']:
            assert 'maintainer_email' not in dataset
