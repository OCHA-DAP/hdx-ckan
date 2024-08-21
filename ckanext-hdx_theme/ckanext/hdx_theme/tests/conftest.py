import pytest

import ckan.tests.factories as factories
import ckan.model as model
import ckan.plugins.toolkit as tk

from typing import cast, Dict
from collections import namedtuple
from ckan.types import Context

from ckanext.hdx_org_group.helpers.static_lists import ORGANIZATION_TYPE_LIST


_get_action = tk.get_action
TestInfo = namedtuple('TestInfo', ['sysadmin_id', 'user_id', 'dataset_id'])

SYSADMIN_USER = 'test_hdx_sysadmin_user'
STANDARD_USER = 'test_hdx_standard_user'
DATASET_NAME = 'dataset_name_for_test_hdx'
LOCATION_NAME = 'location_test_hdx'
ORG_NAME = 'org_name_test_hdx'

@pytest.fixture(scope='module')
def keep_db_tables_on_clean():
    model.repo.tables_created_and_initialised = True


def _get_dataset_dict() -> Dict:
    return {
        'package_creator': 'test function',
        'private': False,
        'dataset_date': '[1960-01-01 TO 2012-12-31]',
        'caveats': 'These are the caveats',
        'license_other': 'TEST OTHER LICENSE',
        'methodology': 'This is a test methodology',
        'dataset_source': 'Test data',
        'license_id': 'hdx-other',
        'name': DATASET_NAME,
        'notes': 'This is a test dataset',
        'title': 'Test Dataset ' + DATASET_NAME,
        'owner_org': ORG_NAME,
        'groups': [{'name': LOCATION_NAME}],
        'data_update_frequency': '30',
        'maintainer': STANDARD_USER
    }


@pytest.fixture()
def dataset_with_uploaded_resource() -> Dict:
    factories.User(name=STANDARD_USER, email='test_hdx_standard_user@hdx.hdxtest.org')
    factories.User(name=SYSADMIN_USER, email='test_hdx_sysadmin_user@hdx.hdxtest.org', sysadmin=True)
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
    dataset_dict = _get_dataset_dict()
    dataset_dict['resources'] = [
        {
            'url': 'hdx_test.csv',
            'url_type': 'upload',
            'resource_type': 'file.upload',
            'format': 'CSV',
            'name': 'hdx_test1.csv',
            'package_id': DATASET_NAME,
        }
    ]
    context = cast(Context,{'model': model, 'session': model.Session, 'user': SYSADMIN_USER})
    created_dataset_dict = _get_action('package_create')(context, dataset_dict)
    return created_dataset_dict
