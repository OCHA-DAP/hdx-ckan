import pytest
import six
import logging as logging
import unicodedata
from bs4 import BeautifulSoup

import ckan.model as model
import ckan.tests.factories as factories

import ckanext.hdx_theme.tests.hdx_test_with_inds_and_orgs as hdx_test_with_inds_and_orgs

import ckan.lib.helpers as h

log = logging.getLogger(__name__)


class TestDataset(hdx_test_with_inds_and_orgs.HDXWithIndsAndOrgsTest):

    def test_edit_dataset_page(self):
        url = h.url_for('hdx_contribute.edit', id='test_dataset_1')
        user = model.User.by_name('testsysadmin')
        result = self.app.get(url, headers={'Authorization': unicodedata.normalize(
            'NFKD', user.apikey).encode('ascii', 'ignore')})

        assert 200 == result.status_code

    def test_edit_dataset_location_order(self):
        factories.Group(name='world')

        url = h.url_for('hdx_contribute.edit', id='test_dataset_1')
        user = model.User.by_name('testsysadmin')
        result = self.app.get(url, headers={'Authorization': unicodedata.normalize(
            'NFKD', user.apikey).encode('ascii', 'ignore')})

        assert 200 == result.status_code

        bs_edit_page = BeautifulSoup(result.data)
        field_locations_options = [i.findAll('option') for i in
                                   bs_edit_page.findAll('select', attrs={'id': 'field_locations'})]

        assert field_locations_options and field_locations_options[0][0].attrs.get(
            'value') == 'world', 'world should be the first entry in locations list'
