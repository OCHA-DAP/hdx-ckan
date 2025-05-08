
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
            'data_update_frequency': '0'
        })

        dataset_2 = self._get_action('package_show')({}, {'id': 'test_dataset_1'})
        assert dataset_2.get('is_fresh') is True, 'any live dataset should be fresh'

        result = self._get_action('package_patch')(context, {
            'id': 'test_dataset_1',
            'data_update_frequency': '7'
        })

        dataset_2 = self._get_action('package_show')({}, {'id': 'test_dataset_1'})
        assert dataset_2.get('is_fresh') is False, 'end of dataset date is used'

        start_date_str = '2020-03-11T21:16:48.838'
        end_date_str = '*'

        date_range = '[{} TO {}]'.format(start_date_str, end_date_str)
        pkg_dict = self._get_action('package_patch')(context,
                                                     {
                                                         'id': 'test_dataset_1',
                                                         'dataset_date': date_range
                                                     })

        dataset_3 = self._get_action('package_show')({}, {'id': 'test_dataset_1'})
        assert dataset_3.get('is_fresh') is True, 'needs to be True as end date is today'
