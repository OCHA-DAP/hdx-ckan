import pytest
import six
import logging as logging
import unicodedata
from unittest import mock
from bs4 import BeautifulSoup

import ckan.model as model
import ckan.tests.factories as factories

import ckanext.hdx_theme.tests.hdx_test_with_inds_and_orgs as hdx_test_with_inds_and_orgs
from ckanext.hdx_users.helpers.permissions import Permissions

import ckan.lib.helpers as h

log = logging.getLogger(__name__)


class TestDataset(hdx_test_with_inds_and_orgs.HDXWithIndsAndOrgsTest):

    def test_edit_dataset_page(self):
        url = h.url_for('hdx_contribute.edit', id='test_dataset_1')
        # user = model.User.by_name('testsysadmin')
        result = self.app.get(url, headers={'Authorization': self.testsysadmin_token})

        assert 200 == result.status_code

    def test_edit_dataset_location_order(self):
        factories.Group(name='world')

        url = h.url_for('hdx_contribute.edit', id='test_dataset_1')
        # user = model.User.by_name('testsysadmin')
        result = self.app.get(url, headers={'Authorization': self.testsysadmin_token})

        assert 200 == result.status_code

        bs_edit_page = BeautifulSoup(result.data)
        field_locations_options = [i.findAll('option') for i in
                                   bs_edit_page.findAll('select', attrs={'id': 'field_locations'})]

        assert field_locations_options and field_locations_options[0][0].attrs.get(
            'value') == 'world', 'world should be the first entry in locations list'

    def _sysadmin_context(self):
        return {'ignore_auth': True, 'model': model, 'session': model.Session, 'user': 'testsysadmin'}

    def _create_qa_dataset(self, name):
        package = {
            'package_creator': 'test function',
            'private': False,
            'dataset_date': '[1960-01-01 TO 2012-12-31]',
            'caveats': 'These are the caveats',
            'license_other': 'TEST OTHER LICENSE',
            'methodology': 'This is a test methodology',
            'dataset_source': 'World Bank',
            'license_id': 'hdx-other',
            'name': name,
            'notes': 'This is a hdxtest dataset for QA',
            'title': 'Test QA Dataset',
            'groups': [{'name': 'roger'}],
            'owner_org': 'hdx-test-org',
            'resources': [
                {'url': 'http://test.test/qa_resource_1.csv', 'format': 'CSV', 'name': 'qa_resource_1.csv',
                 'resource_type': 'api'},
                {'url': 'http://test.test/qa_resource_2.csv', 'format': 'CSV', 'name': 'qa_resource_2.csv',
                 'resource_type': 'api'},
            ]
        }
        return self._get_action('package_create')(self._sysadmin_context(), package)

    def _set_in_quarantine(self, resource_id, value):
        with mock.patch('ckanext.hdx_package.actions.patch.QAQuarantineAnalyticsSender'), \
                mock.patch('ckanext.hdx_package.actions.patch.tag_s3_version_by_resource_id'):
            self._get_action('hdx_mark_resource_in_quarantine')(
                {'model': model, 'session': model.Session, 'user': 'testsysadmin'},
                {'id': resource_id, 'in_quarantine': value})

    def _get_dataset_page(self, name, token=None):
        url = h.url_for('hdx_dataset.read', id=name)
        result = self.app.get(url, headers={'Authorization': token} if token else {})
        assert result.status_code == 200
        return result.body

    def test_qa_controls_for_sysadmins_only(self):
        dataset = self._create_qa_dataset('test_qa_controls_dataset')
        self._set_in_quarantine(dataset['resources'][0]['id'], 'true')

        qa_officer = factories.User(name='test_qa_officer')
        Permissions(qa_officer['name']).set_permissions(self._sysadmin_context(),
                                                        [Permissions.PERMISSION_MANAGE_QA])
        tokens = [None, factories.APIToken(user='tester', expires_in=2, unit=60 * 60)['token'],
                  factories.APIToken(user=qa_officer['name'], expires_in=2, unit=60 * 60)['token']]

        for token in tokens:
            body = self._get_dataset_page('test_qa_controls_dataset', token)
            assert '>Under review<' in body
            assert 'QA actions for' not in body
            assert 'Put all resources under review' not in body
            assert 'qa-bulk-drawer' not in body
            assert 'Download for review' not in body

        body = self._get_dataset_page('test_qa_controls_dataset', self.testsysadmin_token)
        assert '>Under review<' in body
        assert body.count('aria-label="QA actions for') == 2
        assert body.count('data-qa-quarantine="true" data-resource-id') == 1
        assert body.count('data-qa-quarantine="false" data-resource-id') == 1
        assert body.count('Download for review') == 1
        assert 'Put all resources under review' in body
        assert 'Make all resources public' not in body
        assert 'All 2 resources of this dataset will be put under review.' in body

        self._set_in_quarantine(dataset['resources'][1]['id'], 'true')
        body = self._get_dataset_page('test_qa_controls_dataset', self.testsysadmin_token)
        assert 'Make all resources public' in body
        assert 'Put all resources under review' not in body
        assert 'All 2 resources of this dataset will be made public.' in body

    def test_qa_controls_hidden_on_deleted_dataset(self):
        dataset = self._create_qa_dataset('test_qa_deleted_dataset')
        self._set_in_quarantine(dataset['resources'][0]['id'], 'true')
        self._get_action('package_delete')(self._sysadmin_context(), {'id': dataset['id']})

        body = self._get_dataset_page('test_qa_deleted_dataset', self.testsysadmin_token)
        assert '>Under review<' in body
        assert 'QA actions for' not in body
        assert 'Put all resources under review' not in body
        assert 'qa-bulk-drawer' not in body
