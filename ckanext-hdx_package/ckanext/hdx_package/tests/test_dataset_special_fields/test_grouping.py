import datetime
import dateutil.parser as dateutil_parser

import ckan.tests.factories as factories
import ckan.model as model
import ckan.plugins.toolkit as tk

import ckanext.hdx_theme.tests.hdx_test_base as hdx_test_base
from ckanext.hdx_org_group.helpers.static_lists import ORGANIZATION_TYPE_LIST

config = tk.config
ValidationError = tk.ValidationError
_get_action = tk.get_action


class TestGrouping(hdx_test_base.HdxBaseTest):
    context_sysadmin = {'model': model, 'session': model.Session, 'user': 'testsysadmin'}
    dataset_name = 'package-for-testing-grouping'
    resource1_id = None

    daterange_field = 'daterange_for_data'

    modified_3_item_with_A_first_grouping = [
        'Group A',
        'Group C',
        'Group B'
    ]
    modified_3_item_grouping = [
        'Group C',
        'Group B',
        'Group A'
    ]
    original_2_item_grouping = [
        'Group C',
        'Group B'
    ]

    manual_grouping = ['Manual A', 'Manual B']

    @classmethod
    def setup_class(cls):
        super(TestGrouping, cls).setup_class()
        org_id = 'org_name_4_grouping'

        factories.Organization(
            name=org_id,
            title='ORG NAME ' + org_id,
            users=[
                {'name': 'testsysadmin', 'capacity': 'admin'},
            ],
            hdx_org_type=ORGANIZATION_TYPE_LIST[0][1],
            org_url='https://hdx.hdxtest.org/'
        )
        cls.create_package_with_resources(cls.dataset_name, org_id)
        dataset_dict = _get_action('package_show')({}, {'id': cls.dataset_name})
        for r in dataset_dict['resources']:
            if r.get('name') == 'hdx_test1.csv':
                cls.resource1_id = r['id']

    @classmethod
    def create_package_with_resources(cls, pkg_id, org_id):
        package = {
            "package_creator": "test function",
            "private": False,
            "dataset_date": "[1960-01-01 TO 2012-12-31]",
            "caveats": "These are the caveats",
            "license_other": "TEST OTHER LICENSE",
            "methodology": "This is a test methodology",
            "dataset_source": "Test data",
            "license_id": "hdx-other",
            "name": pkg_id,
            "notes": "This is a test dataset",
            "title": "Test Dataset " + pkg_id,
            "owner_org": org_id,
            "groups": [{"name": "roger"}],
            "resources": [
                {
                    'package_id': pkg_id,
                    'url': config.get('ckan.site_url', '') + '/storage/f/test_folder/hdx_test1.csv',
                    'resource_type': 'file.upload',
                    'format': 'CSV',
                    'name': 'hdx_test1.csv',
                    cls.daterange_field: '[2020-04-01T21:16:49 TO 2020-04-12T21:16:49]'
                },
                {
                    'package_id': pkg_id,
                    'url': config.get('ckan.site_url', '') + '/storage/f/test_folder/hdx_test2.csv',
                    'resource_type': 'file.upload',
                    'format': 'CSV',
                    'name': 'hdx_test2.csv',
                    cls.daterange_field: '[2020-04-02T21:16:49 TO 2020-04-12T21:16:49]',
                    'grouping': 'Group B'
                },
                {
                    'package_id': pkg_id,
                    'url': config.get('ckan.site_url', '') + '/storage/f/test_folder/hdx_test3.csv',
                    'resource_type': 'file.upload',
                    'format': 'CSV',
                    'name': 'hdx_test3.csv',
                    cls.daterange_field: '[2020-12-01T21:16:49 TO *]',
                    'grouping': 'Group C'
                }
            ]
        }

        return _get_action('package_create')(cls.context_sysadmin, package)

    def test_dataset_automatic_grouping(self):

        dataset_dict = _get_action('package_show')({}, {'id': self.dataset_name})
        assert dataset_dict.get('x_resource_grouping') == self.original_2_item_grouping

        _get_action('resource_patch')(self.context_sysadmin,
                                      {
                                          'id': self.resource1_id,
                                          'grouping': 'Group A',
                                      })
        dataset_dict = _get_action('package_show')({}, {'id': self.dataset_name})
        assert dataset_dict.get('x_resource_grouping') == self.modified_3_item_grouping

        _get_action('resource_patch')(self.context_sysadmin,
                                      {
                                          'id': self.resource1_id,
                                          self.daterange_field: '[2021-12-01T21:16:49 TO *]'
                                      })
        dataset_dict = _get_action('package_show')({}, {'id': self.dataset_name})
        assert dataset_dict.get('x_resource_grouping') == self.modified_3_item_with_A_first_grouping

        _get_action('resource_patch')(self.context_sysadmin,
                                      {
                                          'id': self.resource1_id,
                                          'grouping': 'Group C',
                                      })
        dataset_dict = _get_action('package_show')({}, {'id': self.dataset_name})
        assert dataset_dict.get('x_resource_grouping') == self.original_2_item_grouping

    def test_dataset_manual_grouping(self):

        _get_action('package_patch')(self.context_sysadmin,
                                     {
                                         'id': self.dataset_name,
                                         'resource_grouping': self.manual_grouping
                                     })
        dataset_dict = _get_action('package_show')({}, {'id': self.dataset_name})
        assert dataset_dict.get('x_resource_grouping') == self.manual_grouping, \
            'computed resource grouping is: {} instead of: {}'.format(
                dataset_dict.get('x_resource_grouping'), self.manual_grouping)
        assert dataset_dict.get('resource_grouping') == dataset_dict.get('x_resource_grouping'), \
            'computed grouping should be same as saved grouping'

        _get_action('resource_patch')(self.context_sysadmin,
                                      {
                                          'id': self.resource1_id,
                                          'grouping': 'Group A',
                                          self.daterange_field: '[2020-04-01T21:16:49 TO 2020-04-12T21:16:49]'
                                      })
        dataset_dict = _get_action('package_show')({}, {'id': self.dataset_name})
        assert dataset_dict.get('x_resource_grouping') == self.manual_grouping
        assert dataset_dict.get('resource_grouping') == dataset_dict.get('x_resource_grouping'), \
            'computed grouping should be same as saved grouping'

        _get_action('package_patch')(self.context_sysadmin,
                                     {
                                         'id': self.dataset_name,
                                         'resource_grouping': None
                                     })
        dataset_dict = _get_action('package_show')({}, {'id': self.dataset_name})
        assert dataset_dict.get('x_resource_grouping') == self.modified_3_item_grouping
        assert not dataset_dict.get('resource_grouping')

