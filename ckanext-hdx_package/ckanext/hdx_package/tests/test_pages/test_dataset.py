import logging as logging
import unicodedata

import ckan.model as model

import ckanext.hdx_theme.tests.hdx_test_with_inds_and_orgs as hdx_test_with_inds_and_orgs

import ckan.lib.helpers as h

log = logging.getLogger(__name__)


class TestDataset(hdx_test_with_inds_and_orgs.HDXWithIndsAndOrgsTest):

    def test_edit_dataset_page(self):
        url = h.url_for(
            controller='ckanext.hdx_package.controllers.contribute_flow_controller:ContributeFlowController',
            action='edit', id='test_dataset_1')
        user = model.User.by_name('testsysadmin')
        result = self.app.get(url, headers={'Authorization': unicodedata.normalize(
            'NFKD', user.apikey).encode('ascii', 'ignore')})

        assert '200' in result.status
