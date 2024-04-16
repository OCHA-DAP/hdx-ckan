import logging as logging

import mock
import pytest

import ckan.lib.helpers as h
import ckan.model as model
import ckan.plugins.toolkit as tk
import ckan.tests.factories as factories
from ckanext.hdx_org_group.tests.test_controller.member_controller_base import MemberControllerBase

_get_action = tk.get_action
NotAuthorized = tk.NotAuthorized
log = logging.getLogger(__name__)

USER = 'some_user'
SYSADMIN = 'testsysadmin'
ORGADMIN = 'orgadmin'
LOCATION = 'some_location'
ORG = 'hdx-test-org'

@pytest.fixture()
def setup_data():
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

@pytest.mark.usefixtures("clean_db", "clean_index", "setup_data")
class TestBulkInviteMembersController(MemberControllerBase):

    @mock.patch('ckanext.hdx_users.helpers.mailer._mail_recipient_html')
    def test_bulk_members_invite(self, _mail_recipient_html, app):
        orgadmin = 'orgadmin'
        context = {'model': model, 'session': model.Session, 'user': orgadmin}
        orgadmin_token = factories.APIToken(user='orgadmin', expires_in=2, unit=60 * 60)['token']
        auth = {'Authorization': orgadmin_token}

        # removing one member from organization
        url = h.url_for('hdx_members.member_delete', id='hdx-test-org')
        result = app.post(url, data={'user': 'johndoe1'}, extra_environ=auth)

        member_list = _get_action('member_list')(context, {
            'id': 'hdx-test-org',
            'object_type': 'user',
            'user_info': True
        })
        deleted_length = len(member_list)
        assert 'John Doe1' not in (m[4] for m in member_list)

        # bulk adding members
        url = h.url_for('hdx_members.bulk_member_new', id='hdx-test-org')

        result = app.post(url, data={'emails': 'janedoe3,johndoe1,another_test@example.com', 'role': 'editor'}, extra_environ=auth)
        context2 = {'model': model, 'session': model.Session, 'user': orgadmin}
        member_list2 = _get_action('member_list')(context2, {
            'id': 'hdx-test-org',
            'object_type': 'user',
            'user_info': True
        })

        assert len(member_list2) == deleted_length + 2, 'Number of members should have increased by 2'
        new_member = next((m for m in member_list2 if 'John Doe1' == m[4]), None)
        assert new_member, 'Invited user needs to be a member of the org'
        assert new_member[3] == 'editor', 'Invited user needs to be an editor'

        # making john doe1 a member back
        result = app.post(url, data={'emails': 'johndoe1', 'role': 'member'}, extra_environ=auth)
        context3 = {'model': model, 'session': model.Session, 'user': orgadmin}
        member_list3 = _get_action('member_list')(context3, {
            'id': 'hdx-test-org',
            'object_type': 'user',
            'user_info': True
        })
        new_member = next((m for m in member_list3 if 'John Doe1' == m[4]), None)
        assert new_member, 'Invited user needs to be a member of the org'
        assert new_member[3] == 'member', 'Invited user needs to be a member'
