import logging as logging

import mock
import pytest

import ckan.lib.helpers as h
import ckan.model as model
import ckan.plugins.toolkit as tk
import ckan.tests.factories as factories
import ckanext.hdx_org_group.tests as org_group_base
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

    @pytest.mark.usefixtures('with_request_context')
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

        result = app.post(url, data={'emails': 'janedoe3,johndoe1,dan@k.ro', 'role': 'editor'}, extra_environ=auth)
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


@pytest.mark.usefixtures('keep_db_tables_on_clean', 'clean_db', 'clean_index', 'setup_user_data',
                         'with_request_context')
class TestMembersController(MemberControllerBase):

    def _populate_member_names(self, members, member_with_name_list):
        ret = [next(u[4] for u in member_with_name_list if u[0] == member[0]) for member in members]
        return ret

    @pytest.mark.usefixtures('with_request_context')
    @mock.patch('ckanext.hdx_org_group.views.members.render')
    def test_members(self, render, app):
        '''
        NOTE: This test might generate some exceptions in the console as the render() method is mocked
        so the ckanext.hdx_org_group.views.members.members() returns a mock object that flask doesn't like.
        '''
        orgadmin = 'orgadmin'
        context = {'model': model, 'session': model.Session, 'user': orgadmin}
        orgadmin_token = factories.APIToken(user='orgadmin', expires_in=2, unit=60 * 60)['token']
        auth = {'Authorization': orgadmin_token}

        member_with_name_list = _get_action('member_list')(context, {
            'id': 'hdx-test-org',
            'object_type': 'user',
            'user_info': True
        })

        # By default the users should be sorted alphabetically asc
        url = h.url_for('hdx_members.members', id='hdx-test-org')
        app.get(url, extra_environ=auth)
        member_list = render.call_args[0][1]['members']
        user_list = self._populate_member_names(member_list, member_with_name_list)

        for idx, val in enumerate(user_list):
            if idx < len(user_list) - 1 and user_list[idx] and user_list[idx + 1]:
                assert user_list[idx] < user_list[idx + 1], "{} should be before {}". \
                    format(user_list[idx], user_list[idx + 1])

        # Sorting alphabetically desc
        sort = 'title desc'
        url = h.url_for('hdx_members.members', id='hdx-test-org', sort=sort)
        app.get(url, extra_environ=auth)
        member_list = render.call_args[0][1]['members']
        user_list = self._populate_member_names(member_list, member_with_name_list)

        for idx, val in enumerate(user_list):
            if idx < len(user_list) - 1 and user_list[idx] and user_list[idx + 1]:
                assert user_list[idx] > user_list[idx + 1], "{} should be before {}". \
                    format(user_list[idx], user_list[idx + 1])

        # Querying
        q = 'john'
        url = h.url_for('hdx_members.members', id='hdx-test-org', q=q)
        result = app.get(url, extra_environ=auth)
        member_list = render.call_args[0][1]['members']
        user_list = self._populate_member_names(member_list, member_with_name_list)

        assert len(user_list) == 1, "Only one user should be found for query"
        assert user_list[0] == 'John Doe1'

@pytest.mark.usefixtures('keep_db_tables_on_clean', 'clean_db', 'clean_index', 'setup_user_data',
                         'with_request_context')
class TestMembersDeleteController(MemberControllerBase):

    def _populate_member_names(self, members, member_with_name_list):
        ret = [next(u[4] for u in member_with_name_list if u[0] == member[0]) for member in members]
        return ret

    @mock.patch('ckanext.hdx_users.helpers.mailer._mail_recipient_html')
    def test_members_delete_add(self, _mail_recipient_html, app):

        orgadmin = 'orgadmin'
        context = {'model': model, 'session': model.Session, 'user': orgadmin}
        orgadmin_obj = model.User.by_name(orgadmin)
        orgadmin_token = factories.APIToken(user='orgadmin', expires_in=2, unit=60 * 60)['token']
        auth = {'Authorization': orgadmin_token}

        url = h.url_for('hdx_members.member_delete', id='hdx-test-org')
        try:
            app.post(url, params={'user': 'johndoe1'}, extra_environ=auth)
        except Exception as ex:
            assert False

        member_list = _get_action('member_list')(context, {
            'id': 'hdx-test-org',
            'object_type': 'user',
            'user_info': True
        })

        deleted_length = len(member_list)
        assert 'John Doe1' not in (m[4] for m in member_list)

        url = h.url_for('hdx_members.member_new', id='hdx-test-org')
        app.post(url, params={'username': 'johndoe1', 'role': 'editor'}, extra_environ=auth)

        member_list2 = _get_action('member_list')(context, {
            'id': 'hdx-test-org',
            'object_type': 'user',
            'user_info': True
        })

        assert len(member_list2) == deleted_length + 1, 'Number of members should have increased by 1'

        member_johndoe1 = next((m for m in member_list2 if m[4] == 'John Doe1'), None)
        assert member_johndoe1, 'User johndoe1 needs to be a member of the org'
        assert member_johndoe1[3] == 'editor', 'User johndoe1 needs to be an editor'

class TestRequestMembershipMembersController(org_group_base.OrgGroupBaseWithIndsAndOrgsTest):

    @classmethod
    def _create_test_data(cls):
        super(TestRequestMembershipMembersController, cls)._create_test_data(create_datasets=False, create_members=True)

    def _populate_member_names(self, members, member_with_name_list):
        ret = [next(u[4] for u in member_with_name_list if u[0] == member[0]) for member in members]
        return ret

    @pytest.mark.usefixtures('with_request_context')
    @mock.patch('ckanext.hdx_users.helpers.mailer._mail_recipient_html')
    def test_request_membership(self, _mail_recipient_html, app):
        test_sysadmin = 'testsysadmin'
        test_username = 'johndoe1'
        test_username_token = factories.APIToken(user=test_username, expires_in=2, unit=60 * 60)['token']
        context = {'model': model, 'session': model.Session, 'user': test_sysadmin}

        # removing one member from organization
        url = h.url_for('hdx_members.member_delete', id='hdx-test-org')
        app.post(url, params={'user': 'johndoe1'}, extra_environ={"REMOTE_USER": test_sysadmin})

        member_list = self._get_action('member_list')(context, {
            'id': 'hdx-test-org',
            'object_type': 'user',
            'user_info': True
        })

        assert 'John Doe1' not in (m[4] for m in member_list)

        # user update - email
        self._get_action('user_update')(context, {'id': test_sysadmin, 'email': 'test@sys.admin'})
        usr_dict = self._get_action('user_show')(context, {'id': test_sysadmin})
        assert usr_dict['email'] == 'test@sys.admin'

        # send a membership request
        url = h.url_for('ytp_request.new')
        ret_page = app.post(url, params={'organization': 'hdx-test-org', 'role': 'member', 'save': 'save',
                                         'message': 'add me to your organization'},
                            headers={'Authorization': test_username_token})
        member_requests = self._get_action('member_request_list')(context, {'group': 'hdx-test-org'})
        assert len(member_requests) == 1, 'Exactly one member request should exist for this org'
        assert member_requests[0].get('user_name') == test_username


class TestMembersDuplicateController(org_group_base.OrgGroupBaseWithIndsAndOrgsTest):

    @classmethod
    def _create_test_data(cls):
        super(TestMembersDuplicateController, cls)._create_test_data(create_datasets=False, create_members=True)

    def _populate_member_names(self, members, member_with_name_list):
        ret = [next(u[4] for u in member_with_name_list if u[0] == member[0]) for member in members]
        return ret

    @pytest.mark.usefixtures('with_request_context')
    @mock.patch('ckanext.hdx_users.helpers.mailer._mail_recipient_html')
    def test_request_membership(self, _mail_recipient_html, app):
        test_sysadmin = 'testsysadmin'
        test_username = 'johndoe1'
        test_username_token = factories.APIToken(user=test_username, expires_in=2, unit=60 * 60)['token']
        context = {'model': model, 'session': model.Session, 'user': test_sysadmin}

        # removing one member from organization
        url = h.url_for('hdx_members.member_delete', id='hdx-test-org')
        app.post(url, params={'user': 'johndoe1'}, extra_environ={"REMOTE_USER": test_sysadmin})

        member_list = self._get_action('member_list')(context, {
            'id': 'hdx-test-org',
            'object_type': 'user',
            'user_info': True
        })

        assert 'John Doe1' not in (m[4] for m in member_list)

        # user update - email
        self._get_action('user_update')(context, {'id': test_sysadmin, 'email': 'test@sys.admin'})
        usr_dict = self._get_action('user_show')(context, {'id': test_sysadmin})
        assert usr_dict['email'] == 'test@sys.admin'

        # send a membership request
        url = h.url_for('ytp_request.new')
        ret_page = app.post(url, params={'organization': 'hdx-test-org', 'role': 'editor', 'save': 'save',
                                         'message': 'add me to your organization'},
                            headers={'Authorization': test_username_token})
        member_requests = self._get_action('member_request_list')(context, {'group': 'hdx-test-org'})
        assert len(member_requests) == 1, 'Exactly one member request should exist for this org'
        assert member_requests[0].get('user_name') == test_username

        member_list = self._get_action('member_list')(context, {
            'id': 'hdx-test-org',
            'object_type': 'user',
            'user_info': True
        })
        assert 'John Doe1' not in (m[4] for m in member_list)

        # bulk adding members
        url = h.url_for('hdx_members.bulk_member_new', id='hdx-test-org')

        self.app.post(url, params={'emails': 'johndoe1', 'role': 'editor'},
                      extra_environ={"REMOTE_USER": test_sysadmin})
        member_list = self._get_action('member_list')(context, {
            'id': 'hdx-test-org',
            'object_type': 'user',
            'user_info': True
        })
        assert 'John Doe1' in (m[4] for m in member_list)

        # approve membership request with new capacity admin instead of editor
        self._get_action("member_request_process")(context, {"member": member_requests[0].get('id'), "role": "admin",
                                                             "approve": True})
        member_list = self._get_action('member_list')(context, {
            'id': 'hdx-test-org',
            'object_type': 'user',
            'user_info': True
        })
        member_list_john = [m for m in member_list if m[4] == 'John Doe1']

        # there should be only 1 member
        assert len(member_list_john) == 1
        assert member_list_john[0][3] == 'admin'
