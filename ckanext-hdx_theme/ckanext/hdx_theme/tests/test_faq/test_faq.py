'''
Created on March 21, 2019

@author: dan mihaila
'''

import unicodedata
import logging as logging

import ckan.model as model
import ckan.lib.helpers as h
import ckan.plugins.toolkit as tk

import ckanext.hdx_theme.tests.hdx_test_base as hdx_test_base
import ckanext.hdx_theme.tests.hdx_test_with_inds_and_orgs as hdx_test_with_inds_and_orgs

log = logging.getLogger(__name__)

contact_form = {
    'topic': 'Getting Started',
    'fullname': 'hdx',
    'email': 'hdx.feedback@gmail.com',
    'faq-mesg': 'my question',
}

class TestFaqController(hdx_test_with_inds_and_orgs.HDXWithIndsAndOrgsTest):

    @classmethod
    def _load_plugins(cls):
        try:
            hdx_test_base.load_plugin('hdx_pages hdx_package hdx_search hdx_org_group hdx_theme')
        except Exception as e:
            log.warn('Module already loaded')
            log.info(str(e))

    @classmethod
    def _get_action(cls, action_name):
        return tk.get_action(action_name)

    @classmethod
    def _create_test_data(cls, create_datasets=True, create_members=False):
        super(TestFaqController, cls)._create_test_data(create_datasets=False, create_members=True)





