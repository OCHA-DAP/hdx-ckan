import pytest
import mock

import datetime

from ckanext.hdx_org_group.helpers.static_lists import ORGANIZATION_TYPE_LIST

from ckanext.hdx_org_group.helpers.data_completness import DataCompletness

from ckanext.hdx_org_group.controllers.country_controller import CountryController

import ckan.model as model
import ckan.plugins.toolkit as tk
import ckan.tests.factories as factories

_get_action = tk.get_action

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

USER = 'some_user'
LOCATION = 'some_location'


def _generate_dataset_dict(dataset_name, org_id, group_name, review_date):
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
        "maintainer": USER
    }

    context = {'model': model, 'session': model.Session, 'user': USER}
    dataset_dict = _get_action('package_create')(context, dataset)
    return dataset_dict


@pytest.fixture()
def setup_data():
    factories.User(name=USER, email='some_user@hdx.hdxtest.org')
    org_name = 'org_name_4_completeness'
    group = factories.Group(name=LOCATION)
    factories.Organization(
        name=org_name,
        title='ORG NAME FOR COMPLETENESS',
        users=[
            {'name': USER, 'capacity': 'editor'},
        ],
        hdx_org_type=ORGANIZATION_TYPE_LIST[0][1],
        org_url='https://hdx.hdxtest.org/'
    )

    review_date1 = datetime.datetime.utcnow() - datetime.timedelta(days=60)
    _generate_dataset_dict('dataset1-category1', org_name, group.get('name'), review_date1)

    review_date2 = datetime.datetime.utcnow()
    _generate_dataset_dict('dataset2-category1', org_name, group.get('name'), review_date2)


@pytest.fixture(scope='module')
def keep_db_tables_on_clean():
    model.repo.tables_created_and_initialised = True


class MockedDataCompleteness(DataCompletness):

    def _fetch_yaml(self):
        return input_yaml_for_1_country


@pytest.mark.usefixtures("keep_db_tables_on_clean", "clean_db", "clean_index", "setup_data")
class TestDataCompleteness(object):

    @mock.patch('ckanext.hdx_org_group.helpers.data_completness.DataCompletness')
    def test_data_completeness(self, patched_DataCompleteness):
        mocked_data_completeness = MockedDataCompleteness(LOCATION, '')
        patched_DataCompleteness.return_value = mocked_data_completeness
        CountryController._get_data_completeness('test_location')
        data = mocked_data_completeness.config

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
