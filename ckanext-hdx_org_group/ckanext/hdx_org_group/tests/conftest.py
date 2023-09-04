import pytest

import ckan.plugins.toolkit as tk
import ckan.tests.factories as factories

from ckan import model as model

USER = 'some_user'
SYSADMIN = 'testsysadmin'
ORGADMIN = 'orgadmin'
LOCATION = 'some_location'
ORG = 'hdx-test-org'

_get_action = tk.get_action
NotAuthorized = tk.NotAuthorized

from ckanext.hdx_theme.tests.conftest import keep_db_tables_on_clean


@pytest.fixture()
def setup_user_data():
    factories.User(name=USER, email='some_user@hdx.hdxtest.org', fullname="Some User",
                   about="Just another Some User test user.")
    factories.User(name='janedoe3', email='janedoe3@hdx.hdxtest.org', fullname="Jane Doe3",
                   about="Just another Jane Doe3 test user.")
    factories.User(name='johndoe1', email='johndoe1@hdx.hdxtest.org', fullname="John Doe1",
                   about="Just another John Doe1 test user.")
    factories.User(name=ORGADMIN, email='orgadmin@hdx.hdxtest.org', fullname="Org Admin",
                   about="Just another Org Admin test user.")
    factories.User(name=SYSADMIN, email='testsysadmin@hdx.hdxtest.org', sysadmin=True, fullname="Test Sysadmin",
                   about="Just another Test Sysadmin test user.")

    syadmin_obj = model.User.get('testsysadmin@hdx.hdxtest.org')
    syadmin_obj.apikey = 'SYSADMIN_API_KEY'
    model.Session.commit()

    user_obj = model.User.get('some_user@hdx.hdxtest.org')
    user_obj.apikey = 'SOME_USER_API_KEY'
    model.Session.commit()

    user_obj = model.User.get('janedoe3@hdx.hdxtest.org')
    user_obj.apikey = 'JANEDOE3_API_KEY'
    model.Session.commit()

    user_obj = model.User.get('johndoe1@hdx.hdxtest.org')
    user_obj.apikey = 'JOHNDOE1_API_KEY'
    model.Session.commit()

    user_obj = model.User.get('orgadmin@hdx.hdxtest.org')
    user_obj.apikey = 'ORGADMIN_API_KEY'
    model.Session.commit()

    group = factories.Group(name=LOCATION)
    factories.Organization(
        name=ORG,
        title='HDX TEST ORG',
        users=[
            {'name': USER, 'capacity': 'member'},
            {'name': 'janedoe3', 'capacity': 'member'},
            {'name': 'johndoe1', 'capacity': 'member'},
            {'name': ORGADMIN, 'capacity': 'admin'}
        ],
        hdx_org_type='donor',
        org_url='https://hdx.hdxtest.org/'
    )
