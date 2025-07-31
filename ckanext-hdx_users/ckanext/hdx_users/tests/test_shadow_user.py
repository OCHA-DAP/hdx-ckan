import logging as logging

import pytest
from ckan.types import Context

import ckan.model as model
import ckan.plugins.toolkit as tk
import ckan.tests.factories as factories


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
    'maintainer': HDX_TEST_USER
}



@pytest.fixture()
def setup_data():
    factories.User(name=SYSADMIN_USER, email='some_user@hdx.hdxtest.org', sysadmin=True)
    # factories.User(name=HDX_TEST_USER, email='hdx_user@hdx.hdxtest.org', sysadmin=False)
    # group = factories.Group(name=LOCATION_NAME)
    # factories.Organization(
    #     name=ORG_NAME,
    #     title='ORG NAME FOR GEOPREVIEW',
    #     users=[
    #         {'name': SYSADMIN_USER, 'capacity': 'admin'},
    #         {'name': HDX_TEST_USER, 'capacity': 'admin'},
    #     ],
    #     hdx_org_type=ORGANIZATION_TYPE_LIST[0][1],
    #     org_url='https://hdx.hdxtest.org/'
    # )

    context = {'model': model, 'session': model.Session, 'user': SYSADMIN_USER}
    # dataset_dict = _get_action('package_create')(context, DATASET_DICT)


@pytest.fixture(scope='module')
def keep_db_tables_on_clean():
    model.repo.tables_created_and_initialised = True


@pytest.mark.usefixtures('keep_db_tables_on_clean', 'hdx_clean_db', 'clean_index', 'setup_data')
class TestShadowAccount(object):

    def test_shadow_account_flow(self):
        email = 'jane@shadow.com'
        user_dict = {
            'name': 'shadow_jane_deleted',
            'fullname': 'Shadow Jane',
            'email': email,
            'password': 'Asdasd123!@#',
            'about': 'Shadow Jane, user',
            'state': 'deleted',
        }

        context_sysadmin: Context = {'ignore_auth': True,
                            'model': model, 'session': model.Session, 'user': SYSADMIN_USER}


        try:
            response = _get_action('hdx_shadow_user_create')(context_sysadmin, {'email':email})
            assert response.get('action_performed') == 'created-shadow-account'

            response = _get_action('user_create')(context_sysadmin, user_dict)

            response = _get_action('hdx_shadow_user_create')(context_sysadmin, {'email': email})
            assert response.get('action_performed') == 'none'

            user_dict['state'] = 'pending'
            user_dict['name'] = 'shadow_jane_pending'
            response = _get_action('user_create')(context_sysadmin, user_dict)

            response = _get_action('hdx_shadow_user_create')(context_sysadmin, {'email': email})
            assert response.get('action_performed') == 'none'

            user_dict['state'] = 'shadow'
            user_dict['name'] = 'shadow_jane_shadow'
            try:
                response = _get_action('user_create')(context_sysadmin, user_dict)
            except Exception as e:
                assert True, "The email address 'jane@shadow.com' belongs to a shadow registered user."

            response = _get_action('hdx_shadow_user_create')(context_sysadmin, {'email': email})
            assert response.get('action_performed') == 'none'

            user_dict['state'] = 'active'
            user_dict['name'] = 'shadow_jane_active'
            response_active_user = _get_action('user_create')(context_sysadmin, user_dict)

            response = _get_action('hdx_shadow_user_create')(context_sysadmin, {'email': email})
            assert response.get('action_performed') == 'none'
            assert response_active_user.get('id') == response.get('id')

            q = model.Session.query(model.User)
            user_list = q.all()

            assert len(user_list) == len(_get_action('user_list')(context_sysadmin, {})) + 2
        except Exception as ex:
            log.error(ex)
            print(ex)
            assert False

    def test_shadow_account_with_active(self):
        email = 'jane@shadow.com'
        user_dict = {
            'name': 'shadow_jane_active',
            'fullname': 'Shadow Jane',
            'email': email,
            'password': 'Asdasd123!@#',
            'about': 'Shadow Jane, user',
            'state': 'active',
        }

        context_sysadmin: Context = {'ignore_auth': True,
                            'model': model, 'session': model.Session, 'user': SYSADMIN_USER}
        try:
            response = _get_action('user_create')(context_sysadmin, user_dict)
            response = _get_action('hdx_shadow_user_create')(context_sysadmin, {'email': email})
            assert response.get('action_performed') == 'none'

            q = model.Session.query(model.User)
            user_list = q.all()
            assert len(user_list) == len(_get_action('user_list')(context_sysadmin, {})) + 1

        except Exception as ex:
            log.error(ex)
            print(ex)
            assert False

    def test_shadow_account_with_shadow(self):
        email = 'jane@shadow.com'
        user_dict = {
            'name': 'shadow_jane_shadow',
            'fullname': 'Shadow Jane',
            'email': email,
            'password': 'Asdasd123!@#',
            'about': 'Shadow Jane, user',
            'state': 'shadow',
        }

        context_sysadmin: Context = {'ignore_auth': True,
                                     'model': model, 'session': model.Session, 'user': SYSADMIN_USER}
        try:
            response = _get_action('user_create')(context_sysadmin, user_dict)
            response = _get_action('hdx_shadow_user_create')(context_sysadmin, {'email': email})
            assert response.get('action_performed') == 'none'

            q = model.Session.query(model.User)
            user_list = q.all()
            assert len(user_list) == len(_get_action('user_list')(context_sysadmin, {})) + 1

        except Exception as ex:
            log.error(ex)
            print(ex)
            assert False


    def test_shadow_account_with_deleted(self):
        email = 'jane@shadow.com'
        user_dict = {
            'name': 'shadow_jane_deleted',
            'fullname': 'Shadow Jane',
            'email': email,
            'password': 'Asdasd123!@#',
            'about': 'Shadow Jane, user',
            'state': 'deleted',
        }

        context_sysadmin: Context = {'ignore_auth': True,
                                     'model': model, 'session': model.Session, 'user': SYSADMIN_USER}
        try:
            response = _get_action('user_create')(context_sysadmin, user_dict)
            response = _get_action('hdx_shadow_user_create')(context_sysadmin, {'email': email})
            assert response.get('action_performed') == 'created-shadow-account'

            q = model.Session.query(model.User)
            user_list = q.all()
            assert len(user_list) == len(_get_action('user_list')(context_sysadmin, {})) + 2

        except Exception as ex:
            log.error(ex)
            print(ex)
            assert False


    def test_shadow_account_with_pending(self):
        email = 'jane@shadow.com'
        user_dict = {
            'name': 'shadow_jane_pending',
            'fullname': 'Shadow Jane',
            'email': email,
            'password': 'Asdasd123!@#',
            'about': 'Shadow Jane, user',
            'state': 'pending',
        }

        context_sysadmin: Context = {'ignore_auth': True,
                                     'model': model, 'session': model.Session, 'user': SYSADMIN_USER}
        try:
            response = _get_action('user_create')(context_sysadmin, user_dict)

            user_dict['name'] = 'shadow_jane_pending1'
            response = _get_action('user_create')(context_sysadmin, user_dict)

            response_shadow = _get_action('hdx_shadow_user_create')(context_sysadmin, {'email': email})
            assert response_shadow.get('action_performed') == 'from-pending-to-shadow'

            q = model.Session.query(model.User)
            user_list = q.all()
            assert len(user_list) == len(_get_action('user_list')(context_sysadmin, {})) + 1

        except Exception as ex:
            log.error(ex)
            print(ex)
            assert False
