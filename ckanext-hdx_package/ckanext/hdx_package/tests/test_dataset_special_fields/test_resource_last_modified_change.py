import pytest
import dateutil.parser as dateutil_parser

import ckan.tests.factories as factories
import ckan.model as model
import ckan.plugins.toolkit as tk
from ckan.types import Context

from ckanext.hdx_org_group.helpers.static_lists import ORGANIZATION_TYPE_LIST

_get_action = tk.get_action
ValidationError = tk.ValidationError

STANDARD_USER = 'some_standard_user'
DATASET_NAME_EXTERNAL_RESOURCE = 'dataset_name_for_resource_url_change_with_external_resource'
DATASET_NAME_UPLOADED_RESOURCE = 'dataset_name_for_resource_url_change_with_uploaded_resource'

LOCATION_NAME = 'some_location_for_resource_url_change'
ORG_NAME = 'org_name_for_resource_url_change'
RESOURCE_LINKED_URL = 'http://test.ckan.test/test.csv'

EXTERNAL_RESOURCE = {
    'url': RESOURCE_LINKED_URL,
    'resource_type': 'api',
    'url_type': 'api',
    'format': 'CSV',
    'name': 'data1.csv',
}

UPLOADED_RESOURCE = {
    'url': 'data1.csv', # tk.config.get('ckan.site_url', '') + '/storage/f/test_folder/data1.csv',
    'resource_type': 'file.upload',
    'url_type': 'upload',
    'format': 'CSV',
    'name': 'data1.csv',
}


def _get_dataset_dict(external_resource: bool):
    dataset_name = DATASET_NAME_EXTERNAL_RESOURCE if external_resource else DATASET_NAME_UPLOADED_RESOURCE
    resource = EXTERNAL_RESOURCE if external_resource else UPLOADED_RESOURCE
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
        "owner_org": ORG_NAME,
        "groups": [{"name": LOCATION_NAME}],
        "data_update_frequency": "30",
        "maintainer": STANDARD_USER,
        "resources": [
            resource
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

    context: Context = {'model': model, 'session': model.Session, 'user': STANDARD_USER}
    external_dataset_dict = _get_action('package_create')(context, _get_dataset_dict(external_resource=True))
    uploaded_dataset_dict = _get_action('package_create')(context, _get_dataset_dict(external_resource=False))


@pytest.mark.usefixtures("keep_db_tables_on_clean", "clean_db", "clean_index", "setup_data")
def test_last_modified_change_for_external_resource():
    context: Context = {'model': model, 'session': model.Session, 'user': STANDARD_USER}
    # get the current 'last_modified' field of the resource
    package_dict = _get_action('package_show')(context, {'id': DATASET_NAME_EXTERNAL_RESOURCE})
    last_modified_before = package_dict['resources'][0]['last_modified']

    # update resource with new description
    resource_dict_modified_description = _get_action('resource_patch')(context, {
        'id': package_dict['resources'][0]['id'],
        'description': 'new description', # changing description
        'name': 'data2.csv' # changing the name
    })
    assert last_modified_before == resource_dict_modified_description['last_modified'], \
        'changing description should not affect last_modified'


    new_url = RESOURCE_LINKED_URL.replace('test.csv', 'test2.csv')
    # update the resource with the new url
    resource_dict_modified_url = _get_action('resource_patch')(context, {
        'id': package_dict['resources'][0]['id'],
        'url': new_url
    })
    last_modified_after = resource_dict_modified_url['last_modified']

    # transform string to dates
    before = dateutil_parser.parse(last_modified_before)
    after = dateutil_parser.parse(last_modified_after)

    assert after > before

@pytest.mark.usefixtures("keep_db_tables_on_clean", "clean_db", "clean_index", "setup_data")
def test_last_modified_change_for_uploaded_resource():
    context: Context = {'model': model, 'session': model.Session, 'user': STANDARD_USER}
    # get the current 'last_modified' field of the resource
    package_dict = _get_action('package_show')(context, {'id': DATASET_NAME_UPLOADED_RESOURCE})
    last_modified_before = package_dict['resources'][0]['last_modified']

    # update resource with new description
    resource_dict_modified_description = _get_action('resource_patch')(context, {
        'id': package_dict['resources'][0]['id'],
        'description': 'new description', # changing description
        'url': 'data1.csv',
        'name': 'data2.csv' # changing the name
    })
    assert last_modified_before == resource_dict_modified_description['last_modified'], \
        'changing description should not affect last_modified'
