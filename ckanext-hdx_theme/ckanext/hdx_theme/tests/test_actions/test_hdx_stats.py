import pytest
import mock

import ckan.model as model
import ckan.tests.factories as factories
import ckan.plugins.toolkit as tk

from ckanext.hdx_org_group.helpers.static_lists import ORGANIZATION_TYPE_LIST

_get_action = tk.get_action
g = tk.g
config = tk.config

SYSADMIN_USER = 'some_sysadmin_user'
DATASET_NAME = 'dataset_name_for_general_stats'
LOCATION_NAME = 'some_location_for_general_stats'
ORG_NAME = 'org_name_for_general_stats'
DATASET_DICT = {
    "package_creator": "test function",
    "private": False,
    "dataset_date": "[1960-01-01 TO 2012-12-31]",
    "caveats": "These are the caveats",
    "license_other": "TEST OTHER LICENSE",
    "methodology": "This is a test methodology",
    "dataset_source": "Test data",
    "license_id": "hdx-other",
    # "name": DATASET_NAME,
    "notes": "This is a test dataset",
    # "title": "Test Dataset " + DATASET_NAME,
    # "owner_org": ORG_NAME,
    "groups": [{"name": LOCATION_NAME}],
    "data_update_frequency": "30",
    "maintainer": SYSADMIN_USER
}

RESOURCE_LIST = [
    {
        'url': config.get('ckan.site_url', '') + '/storage/f/test_folder/hdx_test1.csv',
        'resource_type': 'file.upload',
        'format': 'CSV',
        'name': 'hdx_test1.csv',
    }
]


def _create_dataset(index, with_resources=True, owner_org_index=1):
    context = {'model': model, 'session': model.Session, 'user': SYSADMIN_USER}
    dataset_dict = dict(DATASET_DICT)
    dataset_dict['name'] = DATASET_NAME + str(index)
    dataset_dict['title'] = "Test Dataset " + dataset_dict['name'],
    dataset_dict['owner_org'] = ORG_NAME + str(owner_org_index)

    if with_resources:
        dataset_dict['resources'] = RESOURCE_LIST

    result_dict = _get_action('package_create')(context, dataset_dict)
    return result_dict


def _create_org(index):
    org_name = ORG_NAME + str(index)
    factories.Organization(
        name=org_name,
        title='ORG NAME ' + org_name,
        users=[
            {'name': SYSADMIN_USER, 'capacity': 'editor'},
        ],
        hdx_org_type=ORGANIZATION_TYPE_LIST[0][1],
        org_url='https://hdx.hdxtest.org/'
    )
    return org_name


@pytest.fixture()
def setup_data():
    factories.User(name=SYSADMIN_USER, email='some_user@hdx.hdxtest.org', sysadmin=True)
    g.userobj = model.User.by_name(SYSADMIN_USER)
    group = factories.Group(name=LOCATION_NAME)
    _create_org(1)

    _create_dataset(1)


class FakeResponse:
    def json(self):
        return {'success': True}


@pytest.mark.ckan_config('hdx.analytics.enqueue_url', 'http://localhost/dummy-endpoint')
@pytest.mark.usefixtures('keep_db_tables_on_clean', 'clean_db', 'clean_index', 'with_request_context', 'setup_data')
class TestGeneralStats(object):

    @mock.patch('ckanext.hdx_package.actions.patch.tag_s3_version_by_resource_id')
    @mock.patch('ckanext.hdx_theme.util.analytics_stats.HDXStatsAnalyticsSender._populate_defaults')
    @mock.patch('ckanext.hdx_theme.util.analytics_stats.HDXStatsAnalyticsSender._make_http_call')
    def test_general_datasets_stats(self, make_http_call_mock, populate_defaults_mock, tag_s3_mock):
        make_http_call_mock.return_value = FakeResponse()
        context = {'model': model, 'session': model.Session, 'user': SYSADMIN_USER}
        result = _get_action('hdx_push_general_stats')(context, {})
        assert make_http_call_mock.call_count == 1
        mixpanel_meta = result['mixpanel_meta']
        assert mixpanel_meta['datasets in qa'] == 1
        assert mixpanel_meta['datasets qa completed'] == 0

        pkg_dict = _get_action('package_show')(context, {'id': DATASET_NAME + '1'})

        _get_action('hdx_mark_qa_completed')(context, {
            'id': pkg_dict.get('id'),
            'qa_completed': True,
        })
        result = _get_action('hdx_push_general_stats')(context, {})
        assert make_http_call_mock.call_count == 2
        mixpanel_meta = result['mixpanel_meta']
        assert mixpanel_meta['datasets in qa'] == 0
        assert mixpanel_meta['datasets qa completed'] == 1

        dataset2_dict = _create_dataset(2, with_resources=True)
        _get_action('hdx_qa_resource_patch')(context, {
            'id': dataset2_dict['resources'][0]['id'],
            'in_quarantine': True,
        })
        result2 = _get_action('hdx_push_general_stats')(context, {})
        assert make_http_call_mock.call_count == 3
        mixpanel_meta2 = result2['mixpanel_meta']
        assert mixpanel_meta2['datasets total'] == 2
        assert mixpanel_meta2['datasets with quarantine'] == 1

    @mock.patch('ckanext.hdx_theme.util.analytics_stats.HDXStatsAnalyticsSender._populate_defaults')
    @mock.patch('ckanext.hdx_theme.util.analytics_stats.HDXStatsAnalyticsSender._make_http_call')
    def test_general_org_stats(self, make_http_call_mock, populate_defaults_mock):
        make_http_call_mock.return_value = FakeResponse()
        context = {'model': model, 'session': model.Session, 'user': SYSADMIN_USER}
        result = _get_action('hdx_push_general_stats')(context, {})
        mixpanel_meta = result['mixpanel_meta']
        assert mixpanel_meta['orgs total'] == 1
        assert mixpanel_meta['orgs with datasets'] == 1
        assert mixpanel_meta['orgs updating data in past year'] == 1

        _create_org(2)
        result2 = _get_action('hdx_push_general_stats')(context, {})
        mixpanel_meta2 = result2['mixpanel_meta']
        assert mixpanel_meta2['orgs total'] == 2
        assert mixpanel_meta2['orgs with datasets'] == 1
        assert mixpanel_meta2['orgs updating data in past year'] == 1
