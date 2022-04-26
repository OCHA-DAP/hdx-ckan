'''
Created on June 11, 2019

@author: Dan


'''

import pytest
import logging as logging
import unicodedata
import six
import ckan.logic as logic
import ckan.model as model
import ckan.plugins.toolkit as tk
import ckanext.hdx_theme.tests.hdx_test_base as hdx_test_base
import ckanext.hdx_theme.tests.hdx_test_with_inds_and_orgs as hdx_test_with_inds_and_orgs
import ckanext.hdx_users.helpers.permissions as ph

log = logging.getLogger(__name__)
NotFound = tk.ObjectNotFound
h = tk.h

permission = {
    'permission_manage_carousel': 'permission_manage_carousel',
    'permission_manage_cod': 'permission_manage_cod',
    'permission_manage_crisis': 'permission_manage_crisis',
    'permission_view_request_data': 'permission_view_request_data',
    'update_permissions': 'update'
}

permission_carousel = {
    'permission_manage_carousel': 'permission_manage_carousel',
    'update_permissions': 'update'
}

# @pytest.mark.skipif(six.PY3, reason=u'Tests not ready for Python 3')
class TestHDXControllerPage(hdx_test_with_inds_and_orgs.HDXWithIndsAndOrgsTest):

    @classmethod
    def _load_plugins(cls):
        try:
            hdx_test_base.load_plugin('hdx_users hdx_user_extra hdx_package hdx_org_group hdx_theme')
        except Exception as e:
            log.warn('Module already loaded')
            log.info(str(e))

    @classmethod
    def _get_action(cls, action_name):
        return tk.get_action(action_name)

    @classmethod
    def _create_test_data(cls, create_datasets=True, create_members=False):
        super(TestHDXControllerPage, cls)._create_test_data(create_datasets=True, create_members=True)

    def test_permission_page_load(self):
        url = h.url_for(u'hdx_user_permission.read', id='tester')
        try:
            result = self.app.get(url)
            assert False
        except Exception as ex:
            assert True

        user = model.User.by_name('tester')
        try:
            res = self.app.get(url, headers={'Authorization': unicodedata.normalize(
                'NFKD', user.apikey).encode('ascii', 'ignore')})
            assert False
        except Exception as ex:
            log.info(ex)
            assert True

        sysadmin = model.User.by_name('testsysadmin')
        try:
            res = self.app.get(url, headers={'Authorization': unicodedata.normalize(
                'NFKD', sysadmin.apikey).encode('ascii', 'ignore')})
            assert True
        except Exception as ex:
            log.info(ex)
            assert False

        assert ('200' in res.status), 'HTTP OK'
        for key, value in ph.Permissions.ALL_PERMISSIONS_LABELS_DICT.items():
            assert key in res.body
            assert value in res.body

    def test_manage_permissions(self):
        url = h.url_for(u'hdx_user_permission.read', id='tester')
        test_client = self.get_backwards_compatible_test_client()
        try:
            res = test_client.post(url, params=permission)
            assert False
        except Exception as ex:
            assert True

        tester = model.User.by_name('tester')
        tester.email = 'test@test.com'
        auth = {'Authorization': str(tester.apikey)}
        try:
            res = test_client.post(url, params=permission, extra_environ=auth)
            assert False
        except Exception as ex:
            assert True

        sysadmin = model.User.by_name('testsysadmin')
        sysadmin.email = 'test@test.com'
        auth = {'Authorization': str(sysadmin.apikey)}
        try:
            res = test_client.post(url, params=permission, extra_environ=auth)
        except Exception as ex:
            log.info(ex)
            assert False
        assert ('200' in res.status), 'HTTP OK'

        try:
            res = test_client.get(url, headers={'Authorization': unicodedata.normalize(
                'NFKD', sysadmin.apikey).encode('ascii', 'ignore')})
            assert True
        except Exception as ex:
            log.info(ex)
            assert False

        for key, value in ph.Permissions.ALL_PERMISSIONS_LABELS_DICT.items():
            assert key in res.body
            assert value in res.body
        assert res.body.count(' checked ') == 4

        try:
            res = test_client.post(url, params=permission_carousel, extra_environ=auth)
        except Exception as ex:
            log.info(ex)
            assert False
        assert ('200' in res.status), 'HTTP OK'

        try:
            res = test_client.get(url, headers={'Authorization': unicodedata.normalize(
                'NFKD', sysadmin.apikey).encode('ascii', 'ignore')})
            assert True
        except Exception as ex:
            log.info(ex)
            assert False

        for key, value in ph.Permissions.ALL_PERMISSIONS_LABELS_DICT.items():
            assert key in res.body
            assert value in res.body
        assert res.body.count(' checked ') == 1
