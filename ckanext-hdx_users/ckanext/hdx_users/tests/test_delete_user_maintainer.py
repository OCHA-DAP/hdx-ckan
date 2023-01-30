import logging as logging

import pytest

import ckan.model as model
import ckan.plugins.toolkit as tk
import ckan.tests.factories as factories
import ckan.tests.legacy as legacy_tests
from ckanext.hdx_org_group.helpers.static_lists import ORGANIZATION_TYPE_LIST

_get_action = tk.get_action
ValidationError = tk.ValidationError
NotAuthorized = tk.NotAuthorized
log = logging.getLogger(__name__)

SYSADMIN_USER = 'some_sysadmin_user'
HDX_TEST_USER = 'hdx_test_user'
DATASET_NAME = 'dataset_name_for_maintainer'
LOCATION_NAME = 'some_location_for_maintainer'
ORG_NAME = 'org_name_for_maintainer'
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
    "maintainer": HDX_TEST_USER
}


@pytest.fixture()
def setup_data():
    factories.User(name=SYSADMIN_USER, email='some_user@hdx.hdxtest.org', sysadmin=True)
    factories.User(name=HDX_TEST_USER, email='hdx_user@hdx.hdxtest.org', sysadmin=False)
    group = factories.Group(name=LOCATION_NAME)
    factories.Organization(
        name=ORG_NAME,
        title='ORG NAME FOR GEOPREVIEW',
        users=[
            {'name': SYSADMIN_USER, 'capacity': 'admin'},
            {'name': HDX_TEST_USER, 'capacity': 'admin'},
        ],
        hdx_org_type=ORGANIZATION_TYPE_LIST[0][1],
        org_url='https://hdx.hdxtest.org/'
    )

    context = {'model': model, 'session': model.Session, 'user': SYSADMIN_USER}
    dataset_dict = _get_action('package_create')(context, DATASET_DICT)


@pytest.fixture(scope='module')
def keep_db_tables_on_clean():
    model.repo.tables_created_and_initialised = True


@pytest.mark.usefixtures("keep_db_tables_on_clean", "clean_db", "clean_index", "setup_data")
class TestDeleteuserMaintainer(object):

    def test_delete_user_maintainer(self):

        context_sysadmin = {'ignore_auth': True,
                            'model': model, 'session': model.Session, 'user': SYSADMIN_USER}

        context_hdxtestuser = {'model': model, 'session': model.Session, 'user': HDX_TEST_USER}

        testsysadmin = model.User.by_name(SYSADMIN_USER)
        hdxtestuser = model.User.by_name(HDX_TEST_USER)

        try:
            response = _get_action('user_delete')(context_hdxtestuser, {'id': HDX_TEST_USER})
            assert False
        except NotAuthorized:
            assert True, "A user can not be deleted by a non-sysadmin user"

        try:
            response = _get_action('user_delete')(context_sysadmin, {'id': HDX_TEST_USER})
            assert False
        except NotAuthorized:
            assert True, "A user can not be deleted if it is maintainer for at least one dataset"

        data_dict = self._modify_field(context_sysadmin, testsysadmin, DATASET_NAME, 'maintainer', testsysadmin.id)
        assert data_dict.get('maintainer') == testsysadmin.id

        try:
            response = _get_action('user_delete')(context_sysadmin, {'id': HDX_TEST_USER})
            assert True
        except Exception as ex:
            assert False

        try:
            deleted_hdxtestuser = model.User.by_name(HDX_TEST_USER)
            assert deleted_hdxtestuser.state == 'deleted'
        except Exception as ex:
            assert False

        assert True

    def _modify_field(self, context, user, package_id, key, value):
        modified_fields = {'id': package_id,
                           key: value,
                           }
        _get_action('package_patch')(context, modified_fields)
        pkg_dict = _get_action('package_show')(context, {'id': DATASET_NAME})
        return pkg_dict
