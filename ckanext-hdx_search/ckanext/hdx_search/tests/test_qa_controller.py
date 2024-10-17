import logging as logging
import unicodedata

import ckan.logic as logic
import ckan.model as model
import ckan.plugins.toolkit as tk
import ckan.tests.factories as factories

import ckanext.hdx_theme.helpers.helpers as h
import ckanext.hdx_theme.tests.hdx_test_base as hdx_test_base
import ckanext.hdx_theme.tests.hdx_test_with_inds_and_orgs as hdx_test_with_inds_and_orgs
from ckan.common import config

log = logging.getLogger(__name__)
ValidationError = logic.ValidationError


class TestHDXSearch(hdx_test_with_inds_and_orgs.HDXWithIndsAndOrgsTest):

    USERS_USED_IN_TEST = ['testsysadmin', 'tester']

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

    def test_qa_dashboard(self):

        user = model.User.by_name('tester')

        url = h.url_for('hdx_qa.dashboard')

        result = self._get_url(url, user.apikey)
        assert result.status_code == 403


        token = factories.APIToken(user='testsysadmin', expires_in=2, unit=60 * 60)['token']
        url = h.url_for('hdx_qa.dashboard', page=2)
        qa_dashboard_result = self._get_url(url, token)
        assert qa_dashboard_result.status_code == 200

        config['hdx.qadashboard.enabled'] = False
        result = self._get_url(url, token)
        assert result.status_code == 404

        config['hdx.qadashboard.enabled'] = True
        result = self._get_url(url, token)
        assert result.status_code == 200
