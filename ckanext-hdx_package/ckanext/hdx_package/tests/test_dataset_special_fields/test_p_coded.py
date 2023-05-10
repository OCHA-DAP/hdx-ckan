import pytest

import ckan.tests.factories as factories
import ckan.model as model
import ckan.plugins.toolkit as tk

from ckanext.hdx_org_group.helpers.static_lists import ORGANIZATION_TYPE_LIST
from ckanext.hdx_users.helpers.permissions import Permissions

_get_action = tk.get_action
ValidationError = tk.ValidationError

SYSADMIN_USER = 'some_sysadmin_user'
STANDARD_USER = 'some_standard_user'
DATASET_NAME = 'dataset_name_for_p_codes'
LOCATION_NAME = 'some_location_for_p_codes'
ORG_NAME = 'org_name_for_p_codes'
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
    "maintainer": STANDARD_USER
}

RESOURCE_LINKED_URL = 'http://test.ckan.net/hxlproxy/api/data-preview.csv?url=https%3A%2F%2Ftest.test%2Ftest%2Ftest.csv'


def _create_uploaded_resource(context):
    resource = {
        'url': 'hdx_test.csv',
        'url_type': 'upload',
        'resource_type': 'file.upload',
        'format': 'CSV',
        'name': 'hdx_test1.csv',
        'package_id': DATASET_NAME,
    }
    try:
        resource_dict = _get_action('resource_create')(context, resource)
    except ValidationError as e:
        assert False
    return resource_dict


@pytest.fixture()
def setup_data():
    factories.User(name=STANDARD_USER, email='some_standard_user@hdx.hdxtest.org')
    factories.User(name=SYSADMIN_USER, email='some_sysadmin_user@hdx.hdxtest.org', sysadmin=True)
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

    context = {'model': model, 'session': model.Session, 'user': SYSADMIN_USER}
    dataset_dict = _get_action('package_create')(context, DATASET_DICT)


@pytest.mark.usefixtures("keep_db_tables_on_clean", "clean_db", "clean_index", "setup_data")
class TestPCoded(object):

    def test_p_coded(self):
        context = {'model': model, 'session': model.Session, 'user': STANDARD_USER}
        resource_dict = _create_uploaded_resource(context)

        # Try to set 'p_coded' to False with a standard user by using resource_patch() action.
        # Shouldn't work
        resource_dict_modified = _get_action('resource_patch')(context, {
            'id': resource_dict['id'],
            'p_coded': True,
        })
        assert 'p_coded' not in resource_dict_modified, 'Standard user is not allowed to set p_coded field'

        # Changing 'p_coded' should work as sysadmin
        context_sysadmin = {'model': model, 'session': model.Session, 'user': SYSADMIN_USER}
        resource_dict_modified = _get_action('resource_patch')(context_sysadmin, {
            'id': resource_dict['id'],
            'p_coded': 'true',
        })
        assert resource_dict_modified['p_coded'] is True, 'Sysadmin user is allowed to set p_coded field'

        # Try to set 'p_coded' to False with a standard user by using hdx_p_coded_resource_update() action.
        # Shouldn't work
        resource_dict_modified = _get_action('hdx_p_coded_resource_update')(context, {
            'id': resource_dict['id'],
            'p_coded': False,
        })
        assert resource_dict_modified['p_coded'] is False, 'Standard user is not allowed to set p_coded field'

        # Setting the "Manage P-Codes" permission for the standard user
        # Now this user should be able to set the "p_coded" field via the special hdx_p_coded_resource_update() action
        Permissions(STANDARD_USER).set_permissions(context_sysadmin, [Permissions.PERMISSION_MANAGE_P_CODES])
        resource_dict_modified = _get_action('hdx_p_coded_resource_update')(context, {
            'id': resource_dict['id'],
            'p_coded': False,
        })
        assert resource_dict_modified['p_coded'] is False, 'User with permission is allowed to set p_coded field'


