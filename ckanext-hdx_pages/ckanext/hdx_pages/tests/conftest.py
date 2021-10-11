import pytest

import ckan.plugins.toolkit as tk
import ckan.tests.factories as factories

from ckan import model as model

from ckanext.hdx_pages.tests import USER, SYSADMIN, ORG, LOCATION

_get_action = tk.get_action
NotAuthorized = tk.NotAuthorized


@pytest.fixture()
def setup_user_data():
    factories.User(name=USER, email='some_user@hdx.hdxtest.org')
    factories.User(name=SYSADMIN, email='some_sysadmin@hdx.hdxtest.org', sysadmin=True)

    syadmin_obj = model.User.get('some_sysadmin@hdx.hdxtest.org')
    syadmin_obj.apikey = 'SYSADMIN_API_KEY'
    model.Session.commit()

    user_obj = model.User.get('some_user@hdx.hdxtest.org')
    user_obj.apikey = 'USER_API_KEY'
    model.Session.commit()

    group = factories.Group(name=LOCATION)
    factories.Organization(
        name=ORG,
        title='ORG NAME FOR PAGES',
        users=[
            {'name': USER, 'capacity': 'editor'},
        ],
        hdx_org_type='donor',
        org_url='https://hdx.hdxtest.org/'
    )


@pytest.fixture(scope='module')
def keep_db_tables_on_clean():
    model.repo.tables_created_and_initialised = True
