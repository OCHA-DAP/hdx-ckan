'''
Created on June 11, 2019

@author: Dan


'''

import logging as logging
import unicodedata

import ckan.model as model
import ckan.plugins.toolkit as tk
import ckan.tests.factories as factories

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
        res = self.app.get(url)
        assert res.status_code == 404

        user_token = factories.APIToken(user='tester', expires_in=2, unit=60 * 60)['token']
        res = self.app.get(url, headers={'Authorization': user_token})
        assert res.status_code == 404

        sysadmin_token = factories.APIToken(user='testsysadmin', expires_in=2, unit=60 * 60)['token']
        res = self.app.get(url, headers={'Authorization': sysadmin_token})
        assert res.status_code == 200
        for key, value in ph.Permissions.ALL_PERMISSIONS_LABELS_DICT.items():
            assert key in res.body
            assert value in res.body

    def test_manage_permissions(self):
        url = h.url_for(u'hdx_user_permission.read', id='tester')
        test_client = self.get_backwards_compatible_test_client()

        tester = model.User.by_name('tester')
        tester.email = 'test@test.com'
        tester_token = factories.APIToken(user='tester', expires_in=2, unit=60 * 60)['token']
        auth = {'Authorization': tester_token}
        res = test_client.post(url, params=permission, headers=auth)
        assert res.status_code == 404

        sysadmin = model.User.by_name('testsysadmin')
        sysadmin.email = 'testsysadmin@test.com'
        sysadmin_token = factories.APIToken(user='testsysadmin', expires_in=2, unit=60 * 60)['token']
        auth = {'Authorization': sysadmin_token}
        res = test_client.post(url, params=permission, headers=auth)
        assert res.status_code == 302
        assert res.headers['Location'].endswith(url)

        res = test_client.get(url, headers=auth)
        for key, value in ph.Permissions.ALL_PERMISSIONS_LABELS_DICT.items():
            assert key in res.body
            assert value in res.body
        assert res.body.count('checked="checked"') == 4

        res = test_client.post(url, params=permission_carousel, headers=auth)
        assert res.status_code == 302
        assert res.headers['Location'].endswith(url)

        res = test_client.get(url, headers=auth)
        for key, value in ph.Permissions.ALL_PERMISSIONS_LABELS_DICT.items():
            assert key in res.body
            assert value in res.body
        assert res.body.count('checked="checked"') == 1

    def test_permission_unknown_user(self):
        url = h.url_for(u'hdx_user_permission.read', id='unknown-permission-user')
        test_client = self.get_backwards_compatible_test_client()

        sysadmin = model.User.by_name('testsysadmin')
        sysadmin.email = 'testsysadmin@test.com'
        sysadmin_token = factories.APIToken(user='testsysadmin', expires_in=2, unit=60 * 60)['token']
        auth = {'Authorization': sysadmin_token}

        res = test_client.get(url, headers=auth)
        assert res.status_code == 404

        res = test_client.post(url, params=permission, headers=auth)
        assert res.status_code == 404
