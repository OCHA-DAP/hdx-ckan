import datetime

import ckan.tests.factories as factories

import ckanext.hdx_theme.tests.hdx_test_with_inds_and_orgs as hdx_test_with_inds_and_orgs


class TestFreshness(hdx_test_with_inds_and_orgs.HDXWithIndsAndOrgsTest):

    def test_is_fresh_flag(self):
        dataset_1 = self._get_action('package_show')({}, {'id': 'test_dataset_1'})

        assert dataset_1.get('is_fresh') is False

        res1 = factories.Resource(package_id='test_dataset_1')

        context = {'user': 'testsysadmin'}

        result = self._get_action('package_patch')(context, {
            'id': 'test_dataset_1',
            'data_update_frequency': '7'
        })

        dataset_2 = self._get_action('package_show')({}, {'id': 'test_dataset_1'})
        assert dataset_2.get('is_fresh') is True, 'last_modified is null, so revision_last_modified is used'

        res_last_modified = (datetime.datetime.now() - datetime.timedelta(days=15)).isoformat()
        self._get_action('resource_patch')(context, {
            'id': res1['id'],
            'last_modified': res_last_modified
        })

        dataset_3 = self._get_action('package_show')({}, {'id': 'test_dataset_1'})
        assert dataset_3.get('is_fresh') is False, 'needs to be False, last_modified is more than 7+7 days in the past'
