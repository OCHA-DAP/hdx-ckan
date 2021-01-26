'''
Created on Jun 20, 2018

@author: danmihaila
'''

import logging as logging
import pylons.config as config

import ckan.model as model
import ckan.lib.helpers as h
import ckan.tests.legacy as tests

import ckanext.hdx_theme.tests.hdx_test_base as hdx_test_base
import ckanext.hdx_theme.tests.hdx_test_with_inds_and_orgs as hdx_test_with_inds_and_orgs

log = logging.getLogger(__name__)


class TestHDXPackageShow(hdx_test_with_inds_and_orgs.HDXWithIndsAndOrgsTest):

    @classmethod
    def setup_class(cls):
        cls.USERS_USED_IN_TEST.append('johndoe1')
        super(TestHDXPackageShow, cls).setup_class()

    @classmethod
    def _create_test_data(cls):
        super(TestHDXPackageShow, cls)._create_test_data(create_datasets=True, create_members=True)

    def test_hdx_access_to_private_resource(self):

        testsysadmin = model.User.by_name('testsysadmin')
        johndoe1 = model.User.by_name('johndoe1')
        context = {'model': model,
                   'session': model.Session,
                   'user': 'testsysadmin'}


        # Testing access to the dataset API, to check if maintainer is displayed
        # tests.call_action_api(self.app, 'package_show', id='test_private_dataset_1', status=403)
        # tests.call_action_api(self.app, 'package_show', id='test_private_dataset_1', apikey=tester.apikey, status=403)

        result = tests.call_action_api(self.app, 'package_show', id='test_dataset_1', apikey=testsysadmin.apikey, status=200)
        assert 'maintainer_email' in str(result)
        result = tests.call_action_api(self.app, 'package_show', id='test_dataset_1', apikey=johndoe1.apikey, status=200)
        assert 'maintainer_email' in str(result)
        result = tests.call_action_api(self.app, 'package_show', id='test_dataset_1', status=200)
        assert 'maintainer_email' not in str(result)

        result = tests.call_action_api(self.app, 'package_search', apikey=testsysadmin.apikey, status=200,
                                       q='*:*', fq='name:test_dataset_1')
        assert 'maintainer_email' not in str(result)
