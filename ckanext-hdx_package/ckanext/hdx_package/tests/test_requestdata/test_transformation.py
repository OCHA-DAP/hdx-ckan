import json
import mock
import pytest

import ckan.tests.factories as factories
import ckan.model as model
import ckan.plugins.toolkit as tk

from ckanext.hdx_org_group.helpers.static_lists import ORGANIZATION_TYPE_LIST

_get_action = tk.get_action
ValidationError = tk.ValidationError

SYSADMIN_USER = 'some_sysadmin_user'
DATASET_NAME = 'dataset_name_for_geopreview'
LOCATION_NAME = 'some_location_for_geopreview'
ORG_NAME = 'org_name_for_geopreview'
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
    "maintainer": SYSADMIN_USER
}

@pytest.fixture()
def setup_data():
    factories.User(name=SYSADMIN_USER, email='some_user@hdx.hdxtest.org', sysadmin=True)
    group = factories.Group(name=LOCATION_NAME)
    factories.Organization(
        name=ORG_NAME,
        title='ORG NAME FOR GEOPREVIEW',
        users=[
            {'name': SYSADMIN_USER, 'capacity': 'editor'},
        ],
        hdx_org_type=ORGANIZATION_TYPE_LIST[0][1],
        org_url='https://hdx.hdxtest.org/'
    )

    context = {'model': model, 'session': model.Session, 'user': SYSADMIN_USER}
    dataset_dict = _get_action('package_create')(context, DATASET_DICT)

    resource = {
        'url': tk.config.get('ckan.site_url', '') + '/storage/f/test_folder/hdx_test.csv',
        'resource_type': 'file.upload',
        'format': 'SHP',
        'name': 'hdx_test1.shp.zip',
        'package_id': dataset_dict['id'],
    }
    try:
        resource_dict = _get_action('resource_create')(context, resource)
    except ValidationError as e:
        assert False

@pytest.mark.usefixtures("keep_db_tables_on_clean", "clean_db", "clean_index", "setup_data")
class TestTransformationToRequestdata():
    def test_transformation_to_requestdata(self, app):
        context = {'model': model, 'session': model.Session, 'user': SYSADMIN_USER}
        dataset_dict = _get_action('package_show')(context, {'id': DATASET_NAME})
        request_data_dict = self._get_dataset_post_param(dataset_dict)
        request_data_dict.update(
            {
                'save': 'update-dataset-json',
                'is_requestdata_type': True,
                'file_types': ['csv'],
                'field_names': ['field1', 'field2']
            }
        )

        api_token = factories.APIToken(user=SYSADMIN_USER, expires_in=2, unit=60 * 60)['token']
        auth = {'Authorization': api_token}
        result = app.post('/contribute/edit/{}'.format(request_data_dict.get('id')), params=request_data_dict,
                             extra_environ=auth)
        assert result.status_code == 200

    @staticmethod
    def _get_dataset_post_param(dataset_dict):

        return {
            'id': dataset_dict['id'],
            'title': dataset_dict['title'],
            'name': dataset_dict['name'],
            'private': dataset_dict['private'],
            'notes': dataset_dict.get('notes'),
            'subnational': dataset_dict.get('subnational'),
            'dataset_source': dataset_dict.get('dataset_source'),
            'owner_org': dataset_dict.get('owner_org'),
            'locations': [g['name'] for g in dataset_dict.get('groups', [])],
            'maintainer': dataset_dict['maintainer'],
            'license_id': dataset_dict.get('license_id'),
            'methodology': dataset_dict.get('methodology'),
            'data_update_frequency': dataset_dict.get('data_update_frequency'),
            'dataset_date': dataset_dict.get('dataset_date'),
        }

