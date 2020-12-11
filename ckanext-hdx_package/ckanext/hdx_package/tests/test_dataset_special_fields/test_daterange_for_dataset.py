import ckan.model as model
import ckan.plugins.toolkit as tk

import ckanext.hdx_theme.tests.hdx_test_with_inds_and_orgs as hdx_test_with_inds_and_orgs

ValidationError = tk.ValidationError


class TestDaterangeForDataset(hdx_test_with_inds_and_orgs.HDXWithIndsAndOrgsTest):
    context_sysadmin = {'model': model, 'session': model.Session, 'user': 'testsysadmin'}
    package_id = None
    daterange_field = 'dataset_date'

    @classmethod
    def setup_class(cls):
        super(TestDaterangeForDataset, cls).setup_class()

        dataset_dict = cls._get_action('package_show')(cls.context_sysadmin, {'id': 'test_private_dataset_1'})
        cls.package_id = dataset_dict['id']

    def test_save_update_daterange_field(self):

        context_sysadmin = self.context_sysadmin
        start_date_str = '2020-03-11T21:16:48.838'
        end_date_str = '2020-04-12T21:16:49'

        date_range = '[{} TO {}]'.format(start_date_str, end_date_str)
        pkg_dict = self._get_action('package_patch')(context_sysadmin,
                                                     {
                                                         'id': self.package_id,
                                                         self.daterange_field: date_range
                                                     })
        assert pkg_dict.get(self.daterange_field) == '[2020-03-11T21:16:48.838 TO 2020-04-12T21:16:49]', \
            'the date strings should be [start_datetime TO end_datetime]'

        date_range = '[{} TO {}]'.format(start_date_str, '*')
        pkg_dict = self._get_action('package_patch')(context_sysadmin,
                                                           {
                                                               'id': self.package_id,
                                                               self.daterange_field: date_range
                                                           })
        assert pkg_dict.get(self.daterange_field) == '[2020-03-11T21:16:48.838 TO *]', \
            'the date strings should be [start_datetime TO end_datetime]'

        try:
            pkg_dict = self._get_action('package_patch')(context_sysadmin,
                                               {
                                                   'id': self.package_id,
                                                   self.daterange_field: 'DUMMY STRING'
                                               })
            # assert False
        except ValidationError as e:
            assert True, '{} needs to be a daterange'.format(self.daterange_field)
        except Exception as e:
            assert True, '{} needs to be a daterange'.format(self.daterange_field)

        date_range = '12/01/2020-12/31/2020'
        pkg_dict = self._get_action('package_patch')(context_sysadmin,
                                                           {
                                                               'id': self.package_id,
                                                               self.daterange_field: date_range
                                                           })
        assert pkg_dict.get(self.daterange_field) == '[2020-12-01T00:00:00 TO 2020-12-31T23:59:59]', \
            'the date strings should be [start_datetime TO end_datetime]'

        date_range = '12/01/2020'
        pkg_dict = self._get_action('package_patch')(context_sysadmin,
                                                           {
                                                               'id': self.package_id,
                                                               self.daterange_field: date_range
                                                           })
        assert pkg_dict.get(self.daterange_field) == '[2020-12-01T00:00:00 TO 2020-12-01T23:59:59]', \
            'the date strings should be [start_datetime TO end_datetime]'
