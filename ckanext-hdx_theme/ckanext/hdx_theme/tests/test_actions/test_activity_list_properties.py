import logging
import ckanext.hdx_theme.tests.hdx_test_with_inds_and_orgs as hdx_test_with_inds_and_orgs


log = logging.getLogger(__name__)


class TestActivityProperties(hdx_test_with_inds_and_orgs.HDXWithIndsAndOrgsTest):

    def test_organization_activity_list(self):

        result = self._get_action('organization_activity_list')({}, {'id': 'hdx-test-org'})
        all_keys = (
            data_keys
            for activity in result
            for data in activity.get('data', {}).values()
            for data_keys in data.keys()
        )
        for key in all_keys:
            assert 'email' not in key

    def test_group_activity_list(self):

        result = self._get_action('group_activity_list')({}, {'id': 'roger'})
        all_keys = (
            data_keys
            for activity in result
            for data in activity.get('data', {}).values()
            for data_keys in data.keys()
        )
        for key in all_keys:
            assert 'email' not in key

    def test_user_activity_list(self):

        result = self._get_action('user_activity_list')({}, {'id': 'testsysadmin'})
        all_keys = (
            data_keys
            for activity in result
            for data in activity.get('data', {}).values()
            for data_keys in data.keys()
        )
        for key in all_keys:
            assert 'email' not in key

    def test_package_activity_list(self):

        result = self._get_action('package_activity_list')({}, {'id': 'test_dataset_1'})
        all_keys = (
            data_keys
            for activity in result
            for data in activity.get('data', {}).values()
            for data_keys in data.keys()
        )
        for key in all_keys:
            assert 'email' not in key

    # def test_activity_detail_list(self):
    #     result = self._get_action('package_activity_list')({}, {'id': 'test_dataset_1'})
    #     for item in result:
    #         activity_id = item.get('id')
    #
    #         activity_detail_list = self._get_action('activity_detail_list')({}, {'id': activity_id})
    #         all_keys = (
    #             detail_data_keys
    #             for detail in activity_detail_list
    #             for detail_data in detail.get('data', {}).values()
    #             for detail_data_keys in detail_data.keys()
    #         )
    #         for key in all_keys:
    #             assert 'email' not in key
