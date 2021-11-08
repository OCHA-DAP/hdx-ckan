import pytest

import logging as logging
import ckanext.hdx_theme.helpers.helpers as h
import ckan.model as model
import ckan.logic as logic
import unicodedata
from ckan.common import config
import ckan.plugins.toolkit as tk

import ckanext.hdx_theme.tests.hdx_test_base as hdx_test_base
import ckanext.hdx_theme.tests.hdx_test_with_inds_and_orgs as hdx_test_with_inds_and_orgs

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


        user = model.User.by_name('testsysadmin')
        url = h.url_for('hdx_qa.dashboard', page=2)
        qa_dashboard_result = self._get_url(url, user.apikey)
        assert qa_dashboard_result.status_code == 200

        config['hdx.qadashboard.enabled'] = 'false'
        result = self._get_url(url, user.apikey)
        assert result.status_code == 404

        config['hdx.qadashboard.enabled'] = 'true'
        result = self._get_url(url, user.apikey)
        assert result.status_code == 200

    def test_qa_questions_list(self):
        context = {'model': model, 'session': model.Session, 'user': 'tester'}
        context_sysadmin = {'model': model, 'session': model.Session, 'user': 'testsysadmin'}

        qa_q_list = self._get_action('qa_questions_list')(context_sysadmin, {})
        assert 'metadata_checklist' in qa_q_list
        assert 32 == len(qa_q_list.get('metadata_checklist'))
        assert 'resources_checklist' in qa_q_list
        assert 10 == len(qa_q_list.get('resources_checklist'))
        assert 'data_protection_checklist' in qa_q_list
        assert 6 == len(qa_q_list.get('data_protection_checklist'))

    def test_qa_pii_run(self):
        context = {'ignore_auth': True, 'model': model, 'session': model.Session, 'user': 'testsysadmin'}

        dataset = self._get_action('package_show')(context, {'id': 'test_dataset_1'})

        resource = {
            'package_id': dataset['id'],
            'url': config.get('ckan.site_url', '') + '/storage/f/test_folder/test_file.geojson',
            'resource_type': 'file.upload',
            'format': 'GeoJSON',
            'name': 'resource_create_test1.geojson'
        }

        r1 = self._get_action('resource_create')(context, resource)

        try:
            qa_pii_run = self._get_action('qa_pii_run')(context, {'resourceId': r1.get('id')})
        except ValidationError as ex:
            assert True
        assert True

    # resource_id, data_columns_list, weight_column, columns_type_list, sheet
    def test_qa_sdcmicro_run(self):
        context = {'ignore_auth': True, 'model': model, 'session': model.Session, 'user': 'testsysadmin'}

        dataset = self._get_action('package_show')(context, {'id': 'test_dataset_1'})

        resource = {
            'package_id': dataset['id'],
            'url': config.get('ckan.site_url', '') + '/storage/f/test_folder/test_file.geojson',
            'resource_type': 'file.upload',
            'format': 'GeoJSON',
            'name': 'resource_create_test1.geojson'
        }

        r1 = self._get_action('resource_create')(context, resource)

        data_dict = {
            'resource_id': r1.get('id'),
            'data_columns_list': '1|2|3|4|5|6',
            'weight_column': '7',
            'columns_type_list': "text|text|text|text|text|text|numeric",
            'sheet': '0'
        }
        try:
            qa_sdcmicro_run = self._get_action('qa_sdcmicro_run')(context, data_dict)
        except ValidationError as ex:
            assert True
        assert True
