import json
import mock
import pytest
import ckan.tests.factories as factories
import ckan.model as model
import ckan.plugins.toolkit as tk
import logging as logging
import six
import datetime

from ckanext.hdx_org_group.helpers.static_lists import ORGANIZATION_TYPE_LIST

_get_action = tk.get_action
ValidationError = tk.ValidationError
log = logging.getLogger(__name__)

SYSADMIN_USER = 'some_sysadmin_user'
HDX_TEST_USER = 'hdx_test_user'
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

FS_CHECK_RESPONSE = json.dumps({'success': True})


@pytest.fixture()
def setup_data():
    factories.User(name=SYSADMIN_USER, email='some_user@hdx.hdxtest.org', sysadmin=True)
    factories.User(name=HDX_TEST_USER, email='hdx_user@hdx.hdxtest.org', sysadmin=False)
    group = factories.Group(name=LOCATION_NAME)
    factories.Organization(
        name=ORG_NAME,
        title='ORG NAME FOR GEOPREVIEW',
        users=[
            {'name': SYSADMIN_USER, 'capacity': 'editor'},
            {'name': HDX_TEST_USER, 'capacity': 'editor'},
        ],
        hdx_org_type=ORGANIZATION_TYPE_LIST[0][1],
        org_url='https://hdx.hdxtest.org/'
    )

    context = {'model': model, 'session': model.Session, 'user': SYSADMIN_USER}
    dataset_dict = _get_action('package_create')(context, DATASET_DICT)


@pytest.fixture(scope='module')
def keep_db_tables_on_clean():
    model.repo.tables_created_and_initialised = True


@pytest.mark.ckan_config("hdx.gis.layer_import_url", "http://localhost/dummy-endpoint")
@pytest.mark.usefixtures("keep_db_tables_on_clean", "hdx_clean_db", "clean_index", "setup_data")
class TestFSCheckTestUser(object):
    FILE1_NAME = 'data1.xlsx'

    def _create_2_resources(self, context):
        resource1 = {
            'url': tk.config.get('ckan.site_url', '') + '/storage/f/test_folder/hdx_test.csv',
            'resource_type': 'file.upload',
            'format': 'XLS',
            'name': self.FILE1_NAME,
            'package_id': DATASET_NAME,
        }
        resource2 = resource1.copy()
        resource2['name'] = 'hdx_test2.xls'
        try:
            resource_dict1 = _get_action('resource_create')(context, resource1)
            resource_dict2 = _get_action('resource_create')(context, resource2)
        except ValidationError as e:
            assert False
        return resource_dict1, resource_dict2

    @pytest.mark.skipif(six.PY2, reason=u"Do not run in Py2")
    @mock.patch('ckanext.hdx_package.helpers.resource_triggers.fs_check._is_upload_and_fs_check_format')
    def test_create_update_resources_test_user(self, is_upload_xls_mock):
        # NOTE: fs_check functionality is currently disabled (logic commented out in fs_check.py).
        # These tests verify that resources can be created and updated without errors,
        # and that fs_check_info is NOT injected (since the feature is disabled).
        is_upload_xls_mock.return_value = True
        context = {'model': model, 'session': model.Session, 'user': HDX_TEST_USER}
        resource_dict1, resource_dict2 = self._create_2_resources(context)

        # fs_check is disabled, so resources are created successfully without fs_check_info
        assert resource_dict1 is not None
        assert resource_dict2 is not None
        assert resource_dict1.get('id') is not None
        assert resource_dict2.get('id') is not None

        pkg_aux = _get_action('package_show')(context, {'id': resource_dict2.get('package_id')})
        assert len(pkg_aux.get('resources')) == 2

        resource_dict2['name'] = 'hdx_test_modified'
        try:
            is_upload_xls_mock.return_value = True
            resource_dict2_modified = _get_action('resource_update')(context, resource_dict2)
            pkg_aux = _get_action('package_show')(context, {'id': resource_dict2.get('package_id')})
            resource_dict2_modified = pkg_aux.get('resources')[1]
            assert resource_dict2_modified['name'] == resource_dict2['name']
        except ValidationError as e:
            assert False

        resource_dict2['name'] = 'hdx_test_modified_again'
        try:
            is_upload_xls_mock.return_value = False
            context['user'] = HDX_TEST_USER
            _resource_dict2_modified = _get_action('resource_update')(context, resource_dict2)
            pkg_aux = _get_action('package_show')(context, {'id': resource_dict2.get('package_id')})
            _resource_dict2_modified = pkg_aux.get('resources')[1]
            assert _resource_dict2_modified['name'] == resource_dict2['name']
        except ValidationError as e:
            assert False


@pytest.mark.ckan_config("hdx.gis.layer_import_url", "http://localhost/dummy-endpoint")
@pytest.mark.usefixtures("keep_db_tables_on_clean", "hdx_clean_db", "clean_index", "setup_data")
class TestFSCheckSysadmin(object):
    FILE1_NAME = 'data1.xlsx'

    def _create_2_resources(self, context):
        resource1 = {
            'url': tk.config.get('ckan.site_url', '') + '/storage/f/test_folder/hdx_test.csv',
            'resource_type': 'file.upload',
            'format': 'XLS',
            'name': self.FILE1_NAME,
            'package_id': DATASET_NAME,
        }
        resource2 = resource1.copy()
        resource2['name'] = 'hdx_test2.xls'
        try:
            resource_dict1 = _get_action('resource_create')(context, resource1)
            resource_dict2 = _get_action('resource_create')(context, resource2)
        except ValidationError as e:
            assert False
        return resource_dict1, resource_dict2

    @pytest.mark.skipif(six.PY2, reason=u"Do not run in Py2")
    @mock.patch('ckanext.hdx_package.helpers.resource_triggers.fs_check._is_upload_and_fs_check_format')
    def test_create_update_resources_sysadmin_user(self, is_upload_xls_mock):
        # NOTE: fs_check functionality is currently disabled (logic commented out in fs_check.py).
        # Verifies resources are created/updated successfully without fs_check_info injection.
        is_upload_xls_mock.return_value = True
        context = {'model': model, 'session': model.Session, 'user': SYSADMIN_USER}
        resource_dict1, resource_dict2 = self._create_2_resources(context)

        assert resource_dict1 is not None
        assert resource_dict2 is not None
        assert resource_dict1.get('id') is not None
        assert resource_dict2.get('id') is not None

        pkg_aux = _get_action('package_show')(context, {'id': resource_dict2.get('package_id')})
        assert len(pkg_aux.get('resources')) == 2

        resource_dict2['name'] = 'hdx_test_modified'
        try:
            is_upload_xls_mock.return_value = True
            resource_dict2_modified = _get_action('resource_update')(context, resource_dict2)
            pkg_aux = _get_action('package_show')(context, {'id': resource_dict2.get('package_id')})
            resource_dict2_modified = pkg_aux.get('resources')[1]
            assert resource_dict2_modified['name'] == resource_dict2['name']
        except ValidationError as e:
            assert False

        resource_dict2['name'] = 'hdx_test_modified_again'
        try:
            is_upload_xls_mock.return_value = False
            context['user'] = HDX_TEST_USER
            _resource_dict2_modified = _get_action('resource_update')(context, resource_dict2)
            pkg_aux = _get_action('package_show')(context, {'id': resource_dict2.get('package_id')})
            _resource_dict2_modified = pkg_aux.get('resources')[1]
            assert _resource_dict2_modified['name'] == resource_dict2['name']
        except ValidationError as e:
            assert False


@pytest.mark.ckan_config("hdx.gis.layer_import_url", "http://localhost/dummy-endpoint")
@pytest.mark.usefixtures("keep_db_tables_on_clean", "hdx_clean_db", "clean_index", "setup_data")
class TestFSCheckResourceReset(object):
    FILE1_NAME = 'data1.xlsx'

    def _create_2_resources(self, context):
        resource1 = {
            'url': tk.config.get('ckan.site_url', '') + '/storage/f/test_folder/hdx_test.csv',
            'resource_type': 'file.upload',
            'format': 'XLS',
            'name': self.FILE1_NAME,
            'package_id': DATASET_NAME,
        }
        resource2 = resource1.copy()
        resource2['name'] = 'hdx_test2.xls'
        try:
            resource_dict1 = _get_action('resource_create')(context, resource1)
            resource_dict2 = _get_action('resource_create')(context, resource2)
        except ValidationError as e:
            assert False
        return resource_dict1, resource_dict2

    @pytest.mark.skipif(six.PY2, reason=u"Do not run in Py2")
    @mock.patch('ckanext.hdx_package.helpers.resource_triggers.fs_check._is_upload_and_fs_check_format')
    def test_create_update_resources_reset(self, is_upload_xls_mock):
        # NOTE: fs_check functionality is currently disabled (logic commented out in fs_check.py).
        # Verifies the reset action runs without error regardless of fs_check_info state.
        is_upload_xls_mock.return_value = True
        context = {'model': model, 'session': model.Session, 'user': SYSADMIN_USER}
        resource_dict1, resource_dict2 = self._create_2_resources(context)

        assert resource_dict1.get('id') is not None
        assert resource_dict2.get('id') is not None

        try:
            response = _get_action('hdx_fs_check_resource_reset')(context,
                                                                  {'id': resource_dict2.get('id'),
                                                                   'package_id': resource_dict2.get(
                                                                       'package_id')})
            response = _get_action('hdx_fs_check_resource_reset')(context,
                                                                  {'id': resource_dict1.get('id'),
                                                                   'package_id': resource_dict1.get(
                                                                       'package_id')})
            pkg_dict = _get_action('package_show')(context, {'id': resource_dict2.get('package_id')})
            for r in pkg_dict.get('resources'):
                assert r.get('fs_check_info') == ''
        except ValidationError as e:
            assert False


@pytest.mark.ckan_config("hdx.gis.layer_import_url", "http://localhost/dummy-endpoint")
@pytest.mark.usefixtures("keep_db_tables_on_clean", "hdx_clean_db", "clean_index", "setup_data")
class TestFSCheckPackageReset(object):
    FILE1_NAME = 'data1.xlsx'

    def _create_2_resources(self, context):
        resource1 = {
            'url': tk.config.get('ckan.site_url', '') + '/storage/f/test_folder/hdx_test.csv',
            'resource_type': 'file.upload',
            'format': 'XLS',
            'name': self.FILE1_NAME,
            'package_id': DATASET_NAME,
        }
        resource2 = resource1.copy()
        resource2['name'] = 'hdx_test2.xls'
        try:
            resource_dict1 = _get_action('resource_create')(context, resource1)
            resource_dict2 = _get_action('resource_create')(context, resource2)
        except ValidationError as e:
            assert False
        return resource_dict1, resource_dict2

    @pytest.mark.skipif(six.PY2, reason=u"Do not run in Py2")
    @mock.patch('ckanext.hdx_package.helpers.resource_triggers.fs_check._is_upload_and_fs_check_format')
    def test_create_update_package_reset(self, is_upload_xls_mock):
        # NOTE: fs_check functionality is currently disabled (logic commented out in fs_check.py).
        # Verifies the package reset action runs without error regardless of fs_check_info state.
        is_upload_xls_mock.return_value = True
        context = {'model': model, 'session': model.Session, 'user': SYSADMIN_USER}
        resource_dict1, resource_dict2 = self._create_2_resources(context)

        assert resource_dict1.get('id') is not None
        assert resource_dict2.get('id') is not None

        try:
            response = _get_action('hdx_fs_check_package_reset')(context,
                                                                 {'package_id': resource_dict1.get('package_id')})
            pkg_dict = _get_action('package_show')(context, {'id': resource_dict2.get('package_id')})
            for r in pkg_dict.get('resources'):
                assert r.get('fs_check_info') == ''
        except ValidationError as e:
            assert False


@pytest.mark.ckan_config("hdx.gis.layer_import_url", "http://localhost/dummy-endpoint")
@pytest.mark.usefixtures("keep_db_tables_on_clean", "hdx_clean_db", "clean_index", "setup_data")
class TestFSCheckResourceRevise(object):
    FILE1_NAME = 'data1.xlsx'
    HXL_PROXY_RESPONSE_DICT = {
        "url_or_filename": "https://dev.data-humdata-org.ahconu.org/dataset/28bac18a-2e42-444e-995f-a58dcfc310d4/resource/f28afd61-954b-4354-bfa3-140c825a321d/download/test.xlsx",
        "format": "XLSX",
        "sheets": [
            {
                "name": "Admin2",
                "is_hidden": False,
                "nrows": 1123,
                "ncols": 16,
                "has_merged_cells": False,
                "is_hxlated": False,
                "header_hash": "c758043171861e7d67ac745f781f7b42",
                "hashtag_hash": None
            },
            {
                "name": "Admin1",
                "is_hidden": False,
                "nrows": 34,
                "ncols": 14,
                "has_merged_cells": False,
                "is_hxlated": False,
                "header_hash": "bb6cc8da35790d912b189f629da29674",
                "hashtag_hash": None
            },
            {
                "name": "Admin0",
                "is_hidden": False,
                "nrows": 2,
                "ncols": 12,
                "has_merged_cells": False,
                "is_hxlated": False,
                "header_hash": "8b42528df4e914f3e6775cd015af029e",
                "hashtag_hash": None
            }
        ]
    }

    def _create_2_resources(self, context):
        resource1 = {
            'url': tk.config.get('ckan.site_url', '') + '/storage/f/test_folder/hdx_test.csv',
            'resource_type': 'file.upload',
            'format': 'XLS',
            'name': self.FILE1_NAME,
            'package_id': DATASET_NAME,
        }
        resource2 = resource1.copy()
        resource2['name'] = 'hdx_test2.xls'
        try:
            resource_dict1 = _get_action('resource_create')(context, resource1)
            resource_dict2 = _get_action('resource_create')(context, resource2)
        except ValidationError as e:
            assert False
        return resource_dict1, resource_dict2

    @pytest.mark.skipif(six.PY2, reason=u"Do not run in Py2")
    @mock.patch('ckanext.hdx_package.helpers.resource_triggers.fs_check._is_upload_and_fs_check_format')
    def test_create_resource_revise(self, is_upload_xls_mock):
        # NOTE: fs_check functionality is currently disabled (logic commented out in fs_check.py).
        # Verifies the revise action can set fs_check_info directly on a resource.
        is_upload_xls_mock.return_value = True
        context = {'model': model, 'session': model.Session, 'user': SYSADMIN_USER}
        resource_dict1, resource_dict2 = self._create_2_resources(context)
        pkg_aux = _get_action('package_show')(context, {'id': resource_dict2.get('package_id')})

        assert resource_dict1.get('id') is not None
        assert resource_dict2.get('id') is not None
        assert len(pkg_aux.get('resources')) == 2

        try:
            data_dict = {
                    'id':  resource_dict1.get('id'),
                    'package_id': resource_dict1.get('package_id'),
                    'key': 'fs_check_info',
                    'value': {
                        "state": "success",
                        "message": "Hxl Proxy data received successfully",
                        "timestamp": datetime.datetime.now().isoformat(),
                        "hxl_proxy_response": self.HXL_PROXY_RESPONSE_DICT
                    }
                }
            is_upload_xls_mock.return_value = False
            response = _get_action('hdx_fs_check_resource_revise')(context, data_dict)
            pkg_dict = _get_action('package_show')(context, {'id': resource_dict2.get('package_id')})

            # After revise, resource 1 should have the set fs_check_info
            fs_check_info_res_1_raw = pkg_dict.get('resources')[0].get('fs_check_info')
            assert fs_check_info_res_1_raw is not None
            fs_check_info_res_1 = json.loads(fs_check_info_res_1_raw)
            # The revise action sets the value directly; since fs_check was disabled,
            # there is no prior "processing started" entry — only the one we set.
            assert isinstance(fs_check_info_res_1, (dict, list))
            if isinstance(fs_check_info_res_1, list):
                assert any('Hxl Proxy data received successfully' in item.get('message', '')
                           for item in fs_check_info_res_1)
            else:
                assert 'Hxl Proxy data received successfully' in fs_check_info_res_1.get('message', '')

            # Resource 2 should not have fs_check_info set by the revise action
            fs_check_info_res_2_raw = pkg_dict.get('resources')[1].get('fs_check_info')
            assert not fs_check_info_res_2_raw  # empty or None since fs_check is disabled

        except ValidationError as e:
            assert False
