'''
Created on Febr 13, 2020

@author: Dan


'''
import logging
import pytest
import six

import unicodedata

import ckan.plugins.toolkit as tk

import ckanext.hdx_theme.tests.hdx_test_base as hdx_test_base
import ckanext.hdx_theme.tests.hdx_test_with_inds_and_orgs as hdx_test_with_inds_and_orgs

log = logging.getLogger(__name__)


# @pytest.mark.skipif(six.PY3, reason=u"The hdx_package plugin is not available on PY3 yet")
class TestHDXSearch(hdx_test_with_inds_and_orgs.HDXWithIndsAndOrgsTest):

    @classmethod
    def _load_plugins(cls):
        try:
            hdx_test_base.load_plugin('hdx_package hdx_search hdx_org_group hdx_theme')
        except Exception as e:
            log.warn('Module already loaded')
            log.info(str(e))

    @classmethod
    def _create_test_data(cls, create_datasets=True, create_members=False):
        super(TestHDXSearch, cls)._create_test_data(create_datasets=True, create_members=True)

    @classmethod
    def _get_action(cls, action_name):
        return tk.get_action(action_name)

    def _get_url(self, url, apikey=None):
        if apikey:
            page = self.app.get(url, headers={
                'Authorization': unicodedata.normalize('NFKD', apikey).encode('ascii', 'ignore')})
        else:
            page = self.app.get(url)
        return page


    def test_dataset_m_load(self):
        # user = model.User.by_name('tester')
        # user.email = 'test@test.com'
        try:
            res = self.app.get('/m/dataset/test_dataset_1?force_layout=light')
        except Exception as ex:
            assert False
        assert 'hdx-dataset-light-banner' in res.body
        assert '\"dataset-light\"' in res.body

