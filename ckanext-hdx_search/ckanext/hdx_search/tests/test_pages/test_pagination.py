import pytest
import ckan.tests.factories as factories

import ckan.plugins.toolkit as tk
import ckan.model as model

from ckan.types import Context
from ckanext.hdx_org_group.helpers.static_lists import ORGANIZATION_TYPE_LIST
from ckanext.hdx_theme.tests import hdx_test_util

_url_for = tk.url_for
_get_action = tk.get_action

STANDARD_USER = 'some_standard_user'
LOCATION_NAME = 'some_location'
ORG_NAME1 = 'some_org1'
ORG_NAME2 = 'some_org2'


def _get_dataset_dict(dataset_name, org_name):
    return {
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
        "owner_org": org_name,
        "groups": [{"name": LOCATION_NAME}],
        "data_update_frequency": "30",
        "maintainer": STANDARD_USER,
        "resources": [
            {
                'url': 'http://test.ckan.test/test.csv',
                'resource_type': 'api',
                'url_type': 'api',
                'format': 'CSV',
                'name': 'data1.csv',
            }
        ],
    }


@pytest.fixture()
def setup_data():
    factories.User(name=STANDARD_USER, email='some_standard_user@hdx.hdxtest.org')
    group = factories.Group(name=LOCATION_NAME)
    for org_name in [ORG_NAME1, ORG_NAME2]:
        factories.Organization(
            name=org_name,
            title='ORG NAME FOR HDX_REL_URL',
            users=[
                {'name': STANDARD_USER, 'capacity': 'editor'},
            ],
            hdx_org_type=ORGANIZATION_TYPE_LIST[0][1],
            org_url='https://hdx.hdxtest.org/'
        )

    context: Context = {'model': model, 'session': model.Session, 'user': STANDARD_USER}
    _get_action('package_create')(context, _get_dataset_dict(dataset_name='dataset1',
                                                                                     org_name=ORG_NAME1))
    _get_action('package_create')(context, _get_dataset_dict(dataset_name='dataset2',
                                                                                     org_name=ORG_NAME2))


@pytest.mark.usefixtures('keep_db_tables_on_clean', 'clean_db', 'clean_index', 'setup_data')
def test_pagination_2_valued_filter(app):
    url = _url_for('hdx_dataset.search', organization=[ORG_NAME1, ORG_NAME2], ext_page_size=1)
    response = app.get(url)
    assert response.status_code == 200

    page = response.body

    begin_str = '<a class="page-link" href='
    end_str = '</a>'
    search_item1 = f'organization={ORG_NAME1}'
    search_item2 = f'organization={ORG_NAME2}'

    count_org1 = hdx_test_util.count_string_occurrences(page, search_item1, begin_str, end_str)
    assert count_org1 == 1

    count_org2 = hdx_test_util.count_string_occurrences(page, search_item2, begin_str, end_str)
    assert count_org2 == 1
