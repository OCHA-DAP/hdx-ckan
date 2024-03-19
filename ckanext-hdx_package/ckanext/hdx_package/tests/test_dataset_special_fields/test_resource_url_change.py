import pytest
import dateutil.parser as dateutil_parser

import ckan.tests.factories as factories
import ckan.model as model
import ckan.plugins.toolkit as tk

from ckanext.hdx_org_group.helpers.static_lists import ORGANIZATION_TYPE_LIST

_get_action = tk.get_action
ValidationError = tk.ValidationError

STANDARD_USER = 'some_standard_user'
DATASET_NAME = 'dataset_name_for_resource_url_change'
LOCATION_NAME = 'some_location_for_resource_url_change'
ORG_NAME = 'org_name_for_resource_url_change'
RESOURCE_LINKED_URL = 'http://test.ckan.test/test.csv'
DATASET_DICT = {
    "package_creator": "test function",
    "private": False,
    "dataset_date": "[1960-01-01 TO 2012-12-31]",
    "caveats": "These are the caveats",
    "license_other": "TEST OTHER LICENSE",
    "methodology": "This is a test methodology",
    "dataset_source": "Test data",
    "license_id": "hdx-other",
    "name": DATASET_NAME,
    "notes": "This is a test dataset",
    "title": "Test Dataset " + DATASET_NAME,
    "owner_org": ORG_NAME,
    "groups": [{"name": LOCATION_NAME}],
    "data_update_frequency": "30",
    "maintainer": STANDARD_USER,
    "resources": [
        {
            'package_id': DATASET_NAME,
            'url': RESOURCE_LINKED_URL,
            'resource_type': 'api',
            'url_type': 'api',
            'format': 'CSV',
            'name': 'test.csv'
        }
    ],
}



@pytest.fixture()
def setup_data():
    factories.User(name=STANDARD_USER, email='some_standard_user@hdx.hdxtest.org')
    group = factories.Group(name=LOCATION_NAME)
    factories.Organization(
        name=ORG_NAME,
        title='ORG NAME FOR HDX_REL_URL',
        users=[
            {'name': STANDARD_USER, 'capacity': 'editor'},
        ],
        hdx_org_type=ORGANIZATION_TYPE_LIST[0][1],
        org_url='https://hdx.hdxtest.org/'
    )

    context = {'model': model, 'session': model.Session, 'user': STANDARD_USER}
    dataset_dict = _get_action('package_create')(context, DATASET_DICT)


@pytest.mark.usefixtures("keep_db_tables_on_clean", "clean_db", "clean_index", "setup_data")
def test_resource_url_change():
    context = {'model': model, 'session': model.Session, 'user': STANDARD_USER}
    # get the current 'last_modified' field of the resource
    package_dict = _get_action('package_show')(context, {'id': DATASET_NAME})
    last_modified_before = package_dict['resources'][0]['last_modified']

    new_url = RESOURCE_LINKED_URL.replace('test.csv', 'test2.csv')
    # update the resource with the new url
    resource_dict_modified = _get_action('resource_patch')(context, {
        'id': package_dict['resources'][0]['id'],
        'url': new_url
    })
    last_modified_after = resource_dict_modified['last_modified']

    # transform string to dates
    before = dateutil_parser.parse(last_modified_before)
    after = dateutil_parser.parse(last_modified_after)

    assert after > before



