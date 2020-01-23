import ckan.model as model

import ckanext.hdx_theme.tests.hdx_test_with_inds_and_orgs as hdx_test_with_inds_and_orgs
from ckanext.hdx_package.helpers.constants import UNWANTED_DATASET_PROPERTIES


class TestPropertiesNotInDataset(hdx_test_with_inds_and_orgs.HDXWithIndsAndOrgsTest):

    def test_properties_not_in_dataset(self):
        dataset_name = 'test_dataset_1'
        context_sysadmin = {'model': model, 'session': model.Session, 'user': 'testsysadmin'}

        data_dict = {'id': dataset_name}
        for property in UNWANTED_DATASET_PROPERTIES:
            data_dict[property] = 'test@test.test'

        self._get_action('package_patch')(context_sysadmin, data_dict)

        dataset_dict = self._get_action('package_show')({}, {'id': dataset_name})

        for property in UNWANTED_DATASET_PROPERTIES:
            assert property not in dataset_dict, '{} should not be in dataset'.format(property)
