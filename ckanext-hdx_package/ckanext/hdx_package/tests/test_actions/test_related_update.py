'''
Created on Jan 13, 2015

@author: mbelloti
'''

# -*- coding: utf-8 -*-

import logging as logging
import ckan.plugins.toolkit as tk
import ckan.tests as tests
import ckan.model as model
import ckanext.hdx_theme.tests.hdx_test_base as hdx_test_base
import ckan.lib.helpers as h

log = logging.getLogger(__name__)


log = logging.getLogger(__name__)


class TestHDXPackageUpdate(hdx_test_base.HdxBaseTest):

    @classmethod
    def _load_plugins(cls):
        hdx_test_base.load_plugin('hdx_package hdx_theme')

    @classmethod
    def _get_action(cls, action_name):
        return tk.get_action(action_name)

    def test_related_permissions(self):
        new = h.url_for(controller='related',
                           action='new', id='warandpeace')
        data = {
            "title": "testing_create",
            "url": u"http://ckan.org/feed/",
        }
        res = self.app.post(new, params=data,
                            status=[200,302],
                            extra_environ={"REMOTE_USER": "tester"})
        
        edit = h.url_for(controller='related',
                           action='new', id='warandpeace')

        res = self.app.post(edit, params={"title":"testing_edit"},
                            status=[200,302],
                            extra_environ={"REMOTE_USER": "tester"})
        assert '200' in str(res)

        res = self.app.post(edit, params={"title":"testing_edit2"},
                            status=[200,302],
                            extra_environ={"REMOTE_USER": "testsysadmin"})
        assert '200' in str(res)


