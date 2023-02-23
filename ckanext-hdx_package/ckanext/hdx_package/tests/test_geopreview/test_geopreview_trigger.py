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

GEOPREVIEW_RESPONSE = json.dumps({'success': True})


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


@pytest.mark.ckan_config("hdx.gis.layer_import_url", "http://localhost/dummy-endpoint")
@pytest.mark.usefixtures("keep_db_tables_on_clean", "clean_db", "clean_index", "setup_data")
class TestGeopreviewTrigger(object):

    def _create_2_resources(self, context):
        resource1 = {
            'url': tk.config.get('ckan.site_url', '') + '/storage/f/test_folder/hdx_test.csv',
            'resource_type': 'file.upload',
            'format': 'SHP',
            'name': 'hdx_test1.shp.zip',
            'package_id': DATASET_NAME,
        }
        resource2 = resource1.copy()
        resource2['name'] = 'hdx_test2.shp.zip'
        try:
            resource_dict1 = _get_action('resource_create')(context, resource1)
            resource_dict2 = _get_action('resource_create')(context, resource2)
        except ValidationError as e:
            assert False
        return resource_dict1, resource_dict2

    @mock.patch('ckanext.hdx_package.helpers.resource_triggers.geopreview._get_shape_info_as_json')
    def test_create_update_resources(self, get_shape_info_as_json_mock):
        get_shape_info_as_json_mock.return_value = GEOPREVIEW_RESPONSE
        context = {'model': model, 'session': model.Session, 'user': SYSADMIN_USER}
        resource_dict1, resource_dict2 = self._create_2_resources(context)
        assert get_shape_info_as_json_mock.call_count == 2

        resource_dict2['name'] = 'hdx_test_modified'
        try:
            resource_dict2_modified = _get_action('resource_update')(context, resource_dict2)
            assert resource_dict2_modified['name'] == resource_dict2['name']
        except ValidationError as e:
            assert False
        assert get_shape_info_as_json_mock.call_count == 3

    @mock.patch('ckanext.hdx_package.helpers.resource_triggers.geopreview._get_shape_info_as_json')
    def test_delete_resource(self, get_shape_info_as_json_mock):
        get_shape_info_as_json_mock.return_value = GEOPREVIEW_RESPONSE
        context = {'model': model, 'session': model.Session, 'user': SYSADMIN_USER}
        resource_dict1, resource_dict2 = self._create_2_resources(context)
        assert get_shape_info_as_json_mock.call_count == 2

        try:
            _get_action('resource_delete')(context, {'id': resource_dict2['id']})
            dataset_dict = _get_action('package_show')(context, {'id': DATASET_NAME})
            assert len(dataset_dict['resources']) == 1
        except ValidationError as e:
            assert False
        assert get_shape_info_as_json_mock.call_count == 2

    @mock.patch('ckanext.hdx_package.helpers.resource_triggers.geopreview._get_shape_info_as_json')
    def test_update_package(self, get_shape_info_as_json_mock):
        get_shape_info_as_json_mock.return_value = GEOPREVIEW_RESPONSE
        context = {'model': model, 'session': model.Session, 'user': SYSADMIN_USER}
        resource_dict1, resource_dict2 = self._create_2_resources(context)
        assert get_shape_info_as_json_mock.call_count == 2

        try:
            dataset_dict = DATASET_DICT.copy()
            dataset_dict['notes'] += ' - modified'
            context['allow_partial_update'] = True
            dataset_dict_modified = _get_action('package_update')(context, dataset_dict)
            assert dataset_dict_modified['notes'] == dataset_dict['notes']
            assert len(dataset_dict_modified['resources']) == 2
        except ValidationError as e:
            assert False

        assert get_shape_info_as_json_mock.call_count == 2

        try:
            dataset_dict_modified['resources'][0]['name'] = 'hdx_test1_modified.shp.zip'
            dataset_dict_modified2 = _get_action('package_update')(context, dataset_dict_modified)
            assert dataset_dict_modified2['resources'][0]['name'] == 'hdx_test1_modified.shp.zip'
        except ValidationError as e:
            assert False
        assert get_shape_info_as_json_mock.call_count == 3

    @mock.patch('ckanext.hdx_package.helpers.resource_triggers.geopreview._get_shape_info_as_json')
    def test_revise_package(self, get_shape_info_as_json_mock):
        get_shape_info_as_json_mock.return_value = GEOPREVIEW_RESPONSE
        context = {'model': model, 'session': model.Session, 'user': SYSADMIN_USER}
        resource_dict1, resource_dict2 = self._create_2_resources(context)
        assert get_shape_info_as_json_mock.call_count == 2

        try:
            data_dict = {
                'match__name': DATASET_NAME,
                'update__resources__extend': [
                    {
                        'url': tk.config.get('ckan.site_url', '') + '/storage/f/test_folder/hdx_test.csv',
                        'resource_type': 'file.upload',
                        'format': 'SHP',
                        'name': 'hdx_test3.shp.zip',
                        'package_id': DATASET_NAME,
                    }
                ],
            }
            result = _get_action('package_revise')(context, data_dict)
            assert len(result['package']['resources']) == 3
        except ValidationError as e:
            assert False

        assert get_shape_info_as_json_mock.call_count == 3

    @mock.patch('ckanext.hdx_package.helpers.resource_triggers.geopreview._get_shape_info_as_json')
    def test_reorder_resources(self, get_shape_info_as_json_mock):
        get_shape_info_as_json_mock.return_value = GEOPREVIEW_RESPONSE
        context = {'model': model, 'session': model.Session, 'user': SYSADMIN_USER}
        resource_dict1, resource_dict2 = self._create_2_resources(context)
        assert get_shape_info_as_json_mock.call_count == 2

        r1_id = resource_dict1['id']
        r2_id = resource_dict2['id']
        try:
            data_dict = {
                'id': DATASET_NAME,
                "order": [r2_id, r1_id],

            }
            _get_action('package_resource_reorder')(context, data_dict)
            dataset_dict = _get_action('package_show')(context, {'id': DATASET_NAME})
            assert dataset_dict['resources'][0]['id'] == r2_id
            assert dataset_dict['resources'][1]['id'] == r1_id
        except ValidationError as e:
            assert False
        assert get_shape_info_as_json_mock.call_count == 2
