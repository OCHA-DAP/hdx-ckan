import datetime

import mock
import pytest

import ckan.model as model
import ckan.plugins.toolkit as tk
import ckan.tests.factories as factories

import ckanext.hdx_org_group.helpers.country_helper as grp_h

from ckanext.hdx_org_group.helpers.data_completness import DataCompletness, FLAG_NOT_APPLICABLE
from ckanext.hdx_org_group.helpers.static_lists import ORGANIZATION_TYPE_LIST

_get_action = tk.get_action


USER = 'some_user'
LOCATION = 'some_location'
ORG = 'org_name_4_completeness'


def _generate_test_yaml_dict():
    input_yaml_for_1_country = {
        'inherits_from': None,
        'title': 'Test data completeness',
        'description': None,
        'categories': [
            {
                'title': 'Category 1',
                'data_series': [
                    {
                        'rules': {
                            'exclude': None,
                            'include': [
                                '(name:dataset1-category1)',
                                '(name:dataset2-category1)'
                            ]
                        },
                        'title': 'Subcategory 1',
                        'description': 'sub-description 1',
                        'name': 'sub-category-1'
                    },
                    {
                        'rules': {
                            'exclude': None,
                            'include': [
                                '(name:dataset1-category1)'
                            ]
                        },
                        'title': 'Subcategory 2',
                        'description': 'sub-description 2',
                        'name': 'sub-category-2'
                    }
                ]
            }
        ]
    }
    return input_yaml_for_1_country


def _generate_dataset_dict(dataset_name, org_id, group_name, review_date, user=USER, ignore_auth=False):
    dataset = {
        "package_creator": "test function",
        "private": False,
        "dataset_date": "[1960-01-01 TO 2012-12-31]",
        "caveats": "These are the caveats",
        "license_other": "TEST OTHER LICENSE",
        "methodology": "This is a test methodology",
        "dataset_source": "Test data",
        "license_id": "hdx-other",
        "name": dataset_name,
        "notes": "This is a test dataset",
        "title": "Test Dataset " + dataset_name,
        "owner_org": org_id,
        "groups": [{"name": group_name}],
        "review_date": review_date.isoformat(),
        "data_update_frequency": "30",
        "maintainer": user
    }

    context = {'model': model, 'session': model.Session, 'user': user}
    if ignore_auth:
        context['ignore_auth'] = True
    dataset_dict = _get_action('package_create')(context, dataset)
    return dataset_dict


@pytest.fixture()
def setup_data():
    factories.User(name=USER, email='some_user@hdx.hdxtest.org')
    group = factories.Group(name=LOCATION)
    factories.Organization(
        name=ORG,
        title='ORG NAME FOR COMPLETENESS',
        users=[
            {'name': USER, 'capacity': 'editor'},
        ],
        hdx_org_type=ORGANIZATION_TYPE_LIST[0][1],
        org_url='https://hdx.hdxtest.org/'
    )

    review_date1 = datetime.datetime.utcnow() - datetime.timedelta(days=60)
    _generate_dataset_dict('dataset1-category1', ORG, group.get('name'), review_date1)

    review_date2 = datetime.datetime.utcnow()
    _generate_dataset_dict('dataset2-category1', ORG, group.get('name'), review_date2)


@pytest.fixture(scope='module')
def keep_db_tables_on_clean():
    model.repo.tables_created_and_initialised = True


class MockedDataCompleteness(DataCompletness):

    def __init__(self, yaml_dict):
        self.yaml_dict = yaml_dict
        super(MockedDataCompleteness, self).__init__(LOCATION, '')

    def _fetch_yaml(self):
        return self.yaml_dict


@pytest.mark.usefixtures("keep_db_tables_on_clean", "clean_db", "clean_index", "setup_data")
class TestDataCompleteness(object):

    @mock.patch('ckanext.hdx_org_group.helpers.data_completness.DataCompletness')
    def test_data_completeness(self, patched_DataCompleteness):
        data = self.__compute_data_completeness(_generate_test_yaml_dict(), patched_DataCompleteness)

        general_stats = data['stats']
        assert general_stats['state'] == 'not_good'
        assert general_stats['dataseries_not_good_percentage'] == 0.5
        assert general_stats['not_good_dataseries_num'] == 1

        category1_stats = data['categories'][0]['stats']
        assert category1_stats['dataseries_not_good_percentage'] == 0.5
        assert category1_stats['dataseries_good_percentage'] == 0.5

        subcategory1_stats = data['categories'][0]['data_series'][0]['stats']
        assert subcategory1_stats['state'] == 'good'
        assert subcategory1_stats['good_datasets_num'] == 1
        assert subcategory1_stats['total_datasets_num'] == 2

        subcategory2_stats = data['categories'][0]['data_series'][1]['stats']
        assert subcategory2_stats['state'] == 'not_good'
        assert subcategory2_stats['good_datasets_num'] == 0
        assert subcategory2_stats['total_datasets_num'] == 1

    @mock.patch('ckanext.hdx_org_group.helpers.data_completness.DataCompletness')
    def test_data_completeness_force_incomplete(self, patched_DataCompleteness):
        yaml_dict = _generate_test_yaml_dict()
        incomplete_dataset = 'dataset2-category1'
        incomplete_comment = 'incomplete comment'
        yaml_dict['categories'][0]['data_series'][0]['metadata_overrides'] = [{
            'dataset_name': incomplete_dataset,
            'display_state': 'incomplete',
            'comments': incomplete_comment
        }]
        data = self.__compute_data_completeness(yaml_dict, patched_DataCompleteness)

        subcategory1 = data['categories'][0]['data_series'][0]
        subcategory1_stats = subcategory1['stats']
        assert subcategory1_stats['state'] == 'not_good'
        assert subcategory1_stats['good_datasets_num'] == 0
        assert subcategory1_stats['total_datasets_num'] == 2

        dataset = next(d for d in subcategory1['datasets'] if d['name'] == incomplete_dataset)
        assert dataset['general_comment'] == incomplete_comment

    @mock.patch('ckanext.hdx_org_group.helpers.data_completness.DataCompletness')
    def test_data_completeness_force_complete(self, patched_DataCompleteness):
        yaml_dict = _generate_test_yaml_dict()
        complete_dataset = 'dataset1-category1'
        complete_comment = 'complete comment'
        yaml_dict['categories'][0]['data_series'][0]['metadata_overrides'] = [{
            'dataset_name': complete_dataset,
            'display_state': 'complete',
            'comments': complete_comment
        }]
        data = self.__compute_data_completeness(yaml_dict, patched_DataCompleteness)

        subcategory1 = data['categories'][0]['data_series'][0]
        subcategory1_stats = subcategory1['stats']
        assert subcategory1_stats['state'] == 'good'
        assert subcategory1_stats['good_datasets_num'] == 2
        assert subcategory1_stats['total_datasets_num'] == 2

        dataset = next(d for d in subcategory1['datasets'] if d['name'] == complete_dataset)
        assert dataset['general_comment'] == complete_comment

    @mock.patch('ckanext.hdx_org_group.helpers.data_completness.DataCompletness')
    def test_data_completeness_not_available(self, patched_DataCompleteness):
        yaml_dict = _generate_test_yaml_dict()
        not_applicable_comment = 'not applicable comment'
        yaml_dict['categories'][0]['data_series'][1]['flags'] = [{
            'key': FLAG_NOT_APPLICABLE,
            'comments': not_applicable_comment
        }]

        data = self.__compute_data_completeness(yaml_dict, patched_DataCompleteness)

        general_stats = data['stats']
        assert general_stats['state'] == 'good'

        category1_stats = data['categories'][0]['stats']
        assert category1_stats['good_dataseries_num'] == 1
        assert category1_stats['not_good_dataseries_num'] == 0
        assert category1_stats['total_dataseries_num'] == 1

        assert category1_stats['dataseries_good_percentage'] == 1.0

        subcategory1_stats = data['categories'][0]['data_series'][1]['stats']
        assert subcategory1_stats['state'] == FLAG_NOT_APPLICABLE
        assert subcategory1_stats['state_comment'] == not_applicable_comment
        assert subcategory1_stats['good_datasets_num'] == 0
        assert subcategory1_stats['total_datasets_num'] == 0

    @mock.patch('ckanext.hdx_org_group.helpers.data_completness.DataCompletness')
    def test_data_completeness_dataset_up_to_date(self, patched_DataCompleteness):
        review_date = datetime.datetime.utcnow() - datetime.timedelta(days=31)
        _generate_dataset_dict('dataset3-category1', ORG, LOCATION, review_date)
        yaml_dict = _generate_test_yaml_dict()
        yaml_dict['categories'][0]['data_series'].append({
            'rules': {
                'exclude': None,
                'include': [
                    '(name:dataset3-category1)'
                ]
            },
            'title': 'Subcategory 3',
            'description': 'sub-description 3',
            'name': 'sub-category-3'
        })

        data = self.__compute_data_completeness(yaml_dict, patched_DataCompleteness)

        subcategory3_stats = data['categories'][0]['data_series'][2]['stats']
        assert subcategory3_stats['state'] == 'good'
        assert subcategory3_stats['good_datasets_num'] == 1

    def __compute_data_completeness(self, yaml_dict, patched_DataCompleteness):
        mocked_data_completeness = MockedDataCompleteness(yaml_dict)
        patched_DataCompleteness.return_value = mocked_data_completeness
        grp_h._get_data_completeness('test_location')
        data = mocked_data_completeness.config
        return data
