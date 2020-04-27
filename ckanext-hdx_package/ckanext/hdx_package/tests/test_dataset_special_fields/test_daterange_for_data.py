import datetime
import dateutil.parser as dateutil_parser

import ckan.model as model
import ckan.plugins.toolkit as tk

import ckanext.hdx_theme.tests.hdx_test_with_inds_and_orgs as hdx_test_with_inds_and_orgs

ValidationError = tk.ValidationError


class TestResourceDaterangeForData(hdx_test_with_inds_and_orgs.HDXWithIndsAndOrgsTest):
    context_sysadmin = {'model': model, 'session': model.Session, 'user': 'testsysadmin'}
    resource_id = None

    @classmethod
    def setup_class(cls):
        super(TestResourceDaterangeForData, cls).setup_class()

        dataset_dict = cls._get_action('package_show')(cls.context_sysadmin, {'id': 'test_private_dataset_1'})
        cls.resource_id = dataset_dict['resources'][0]['id']

    def test_save_update_daterange_field(self):

        daterange_field = 'daterange_for_data'
        context_sysadmin = self.context_sysadmin
        start_date_str = '2020-03-11T21:16:48.838350'
        end_date_str = '2020-04-12T21:16:49'

        date_range = '[{} TO {}]'.format(start_date_str, end_date_str)
        resource_dict = self._get_action('resource_patch')(context_sysadmin,
                                                           {
                                                               'id': self.resource_id,
                                                               daterange_field: date_range
                                                           })
        assert resource_dict.get(daterange_field) == '[2020-03-11T21:16:48.838 TO 2020-04-12T21:16:49]', \
            'the date strings should be reduced to 23 characters for solr\'s benefit'

        date_range = '[{} TO {}]'.format(start_date_str, '*')
        resource_dict = self._get_action('resource_patch')(context_sysadmin,
                                                           {
                                                               'id': self.resource_id,
                                                               daterange_field: date_range
                                                           })
        assert resource_dict.get(daterange_field) == '[2020-03-11T21:16:48.838 TO *]', \
            'the date strings should be reduced to 23 characters for solr\'s benefit'

        try:
            self._get_action('resource_patch')(context_sysadmin,
                                               {
                                                   'id': self.resource_id,
                                                   daterange_field: 'DUMMY STRING'
                                               })
            assert False
        except ValidationError as e:
            assert True, '{} needs to be a daterange'.format(daterange_field)
        del resource_dict[daterange_field]
        resource_dict2 = self._get_action('resource_update')(context_sysadmin, resource_dict)
        assert not resource_dict2.get(daterange_field), 'For now, {} shouldn\'t be mandatory'.format(daterange_field)

    def test_search_by_daterange_field(self):

        daterange_field = 'daterange_for_data'
        context_sysadmin = self.context_sysadmin
        start_date_str = '2020-03-11T21:16:48.838350'
        start_date = dateutil_parser.parse(start_date_str)
        end_date_str = '2020-04-12T21:16:49'
        end_date = dateutil_parser.parse(end_date_str)

        date_range = '[{} TO {}]'.format(start_date_str, end_date_str)
        resource_dict = self._get_action('resource_patch')(context_sysadmin,
                                                           {
                                                               'id': self.resource_id,
                                                               daterange_field: date_range
                                                           })
        assert resource_dict.get(daterange_field) == '[2020-03-11T21:16:48.838 TO 2020-04-12T21:16:49]', \
                'the date strings should be reduced to 23 characters for solr\'s benefit'

        assert 'test_private_dataset_1' in self.__search_by_date_field(daterange_field, start_date)
        assert 'test_private_dataset_1' in self.__search_by_date_field(daterange_field, end_date)
        assert 'test_private_dataset_1' not in \
               self.__search_by_date_field(daterange_field,dateutil_parser.parse('1999-04-12T21:16:48'))

    def __search_by_date_field(self, daterange_field, around_date):

        begin = around_date - datetime.timedelta(days=5)
        end = around_date + datetime.timedelta(days=5)
        search_dict = {
            'include_private': True,
            'fq': 'res_extras_{}:[{}Z TO {}Z]'.format(daterange_field, begin.isoformat(), end.isoformat())
        }
        results = self._get_action('package_search')(self.context_sysadmin, search_dict)
        return (p.get('name') for p in results.get('results', []))
