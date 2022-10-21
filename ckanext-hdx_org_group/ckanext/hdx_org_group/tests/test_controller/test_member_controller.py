'''
Created on Jun 23, 2015

@author: alexandru-m-g
'''

import logging
import mock
import ckan.model as model
import ckan.lib.helpers as h

import ckanext.hdx_org_group.tests as org_group_base

log = logging.getLogger(__name__)


class TestMembersController(org_group_base.OrgGroupBaseWithIndsAndOrgsTest):

    @classmethod
    def _create_test_data(cls):
        super(TestMembersController, cls)._create_test_data(create_datasets=False, create_members=True)

    def _populate_member_names(self, members, member_with_name_list):
        ret = [next(u[4] for u in member_with_name_list if u[0] == member[0]) for member in members]
        return ret

    @mock.patch('ckanext.hdx_org_group.views.members.render')
    def test_members(self, render):
        test_sysadmin = 'testsysadmin'
        context = {'model': model, 'session': model.Session, 'user': 'testsysadmin'}
        test_client = self.get_backwards_compatible_test_client()

        member_with_name_list = self._get_action('member_list')(context, {
            'id': 'hdx-test-org',
            'object_type': 'user',
            'user_info': True
        })

        # By default the users should be sorted alphabetically asc
        url = h.url_for('hdx_members.members', id='hdx-test-org')
        test_client.get(url, extra_environ={"REMOTE_USER": test_sysadmin})
        member_list = render.call_args[0][1]['members']
        user_list = self._populate_member_names(member_list, member_with_name_list)

        for idx, val in enumerate(user_list):
            if idx < len(user_list) - 1 and user_list[idx] and user_list[idx + 1]:
                assert user_list[idx] < user_list[idx + 1], "{} should be before {}". \
                    format(user_list[idx], user_list[idx + 1])

        # Sorting alphabetically desc
        sort = 'title desc'
        url = h.url_for('hdx_members.members', id='hdx-test-org', sort=sort)
        test_client.get(url, extra_environ={"REMOTE_USER": test_sysadmin})
        member_list = render.call_args[0][1]['members']
        user_list = self._populate_member_names(member_list, member_with_name_list)

        for idx, val in enumerate(user_list):
            if idx < len(user_list) - 1 and user_list[idx] and user_list[idx + 1]:
                assert user_list[idx] > user_list[idx + 1], "{} should be before {}". \
                    format(user_list[idx], user_list[idx + 1])

        # Querying
        q = 'anna'
        url = h.url_for('hdx_members.members', id='hdx-test-org', q=q)
        test_client.get(url, extra_environ={"REMOTE_USER": test_sysadmin})
        member_list = render.call_args[0][1]['members']
        user_list = self._populate_member_names(member_list, member_with_name_list)

        assert len(user_list) == 1, "Only one user should be found for query"
        assert user_list[0] == 'Anna Anderson2'

    @mock.patch('ckanext.hdx_users.helpers.mailer._mail_recipient_html')
    def test_members_delete_add(self, _mail_recipient_html):
        test_client = self.get_backwards_compatible_test_client()

        url = h.url_for('hdx_members.member_delete', id='hdx-test-org')
        try:
            test_client.post(url, params={'user': 'annaanderson2'}, extra_environ={"REMOTE_USER": "testsysadmin"})
        except Exception as ex:
            assert False

        context = {'model': model, 'session': model.Session, 'user': 'testsysadmin'}
        member_list = self._get_action('member_list')(context, {
            'id': 'hdx-test-org',
            'object_type': 'user',
            'user_info': True
        })

        deleted_length = len(member_list)
        assert 'Anna Anderson2' not in (m[4] for m in member_list)

        url = h.url_for('hdx_members.member_new', id='hdx-test-org')
        test_client.post(url, params={'username': 'annaanderson2', 'role': 'editor'},
                      extra_environ={"REMOTE_USER": "testsysadmin"})

        member_list2 = self._get_action('member_list')(context, {
            'id': 'hdx-test-org',
            'object_type': 'user',
            'user_info': True
        })

        assert len(member_list2) == deleted_length + 1, 'Number of members should have increased by 1'

        member_anna = next((m for m in member_list2 if m[4] == 'Anna Anderson2'), None)
        assert member_anna, 'User annaanderson2 needs to be a member of the org'
        assert member_anna[3] == 'editor', 'User annaanderson2 needs to be an editor'

    # def test_members_invite(self):
    #
    #     original_send_invite = mailer.send_invite
    #
    #     def mock_send_invite(user):
    #         global invited_user
    #         invited_user = user
    #
    #     mailer.send_invite = mock_send_invite
    #
    #     context = {
    #         'model': model, 'session': model.Session, 'user': 'testsysadmin'}
    #     url = h.url_for(
    #         controller='ckanext.hdx_org_group.controllers.member_controller:HDXOrgMemberController',
    #         action='member_new',
    #         id='hdx-test-org'
    #     )
    #     self.app.post(url, params={'email': 'hdxtestuser123@test.test', 'role': 'editor'},
    #                   extra_environ={"REMOTE_USER": "testsysadmin"})
    #     org = self._get_action('organization_show')(context, {'id': 'hdx-test-org'})
    #
    #     new_member = next((user for user in org['users'] if 'hdxtestuser123' in user['name']), None)
    #     assert new_member, 'Invited user needs to be a member of the org'
    #     assert new_member['capacity'] == 'editor', 'Invited user needs to be an editor'
    #
    #     mailer.send_invite = original_send_invite
    #

    @mock.patch('ckanext.hdx_users.helpers.mailer._mail_recipient_html')
    def test_bulk_members_invite(self, _mail_recipient_html):
        test_username = 'testsysadmin'

        context = {'model': model, 'session': model.Session, 'user': test_username}

        # removing one member from organization
        url = h.url_for('hdx_members.member_delete', id='hdx-test-org')
        self.app.post(url, params={'user': 'johndoe1'}, extra_environ={"REMOTE_USER": test_username})

        member_list = self._get_action('member_list')(context, {
            'id': 'hdx-test-org',
            'object_type': 'user',
            'user_info': True
        })
        deleted_length = len(member_list)
        assert 'John Doe1' not in (m[4] for m in member_list)

        # bulk adding members
        url = h.url_for('hdx_members.bulk_member_new', id='hdx-test-org')

        self.app.post(url, params={'emails': 'janedoe3,johndoe1,dan@k.ro', 'role': 'editor'},
                      extra_environ={"REMOTE_USER": test_username})
        member_list2 = self._get_action('member_list')(context, {
            'id': 'hdx-test-org',
            'object_type': 'user',
            'user_info': True
        })

        assert len(member_list2) == deleted_length + 2, 'Number of members should have increased by 2'
        new_member = next((m for m in member_list2 if 'John Doe1' == m[4]), None)
        assert new_member, 'Invited user needs to be a member of the org'
        assert new_member[3] == 'editor', 'Invited user needs to be an editor'

        # making john doe1 a member back
        self.app.post(url, params={'emails': 'johndoe1', 'role': 'member'},
                      extra_environ={"REMOTE_USER": test_username})
        member_list3 = self._get_action('member_list')(context, {
            'id': 'hdx-test-org',
            'object_type': 'user',
            'user_info': True
        })
        new_member = next((m for m in member_list3 if 'John Doe1' == m[4]), None)
        assert new_member, 'Invited user needs to be a member of the org'
        assert new_member[3] == 'member', 'Invited user needs to be a member'

    @mock.patch('ckanext.hdx_users.helpers.mailer._mail_recipient_html')
    def test_request_membership(self, _mail_recipient_html):
        test_sysadmin = 'testsysadmin'
        test_username = 'johndoe1'
        test_client = self.get_backwards_compatible_test_client()
        context = {'model': model, 'session': model.Session, 'user': test_sysadmin}

        # removing one member from organization
        url = h.url_for('hdx_members.member_delete', id='hdx-test-org')
        test_client.post(url, params={'user': 'johndoe1'}, extra_environ={"REMOTE_USER": test_sysadmin})

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
        ret_page = test_client.post(url, params={'organization': 'hdx-test-org', 'role': 'member', 'save': 'save',
                                   'message': 'add me to your organization'},
                      extra_environ={"REMOTE_USER": test_username})
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

    @mock.patch('ckanext.hdx_users.helpers.mailer._mail_recipient_html')
    def test_request_membership(self, _mail_recipient_html):
        test_sysadmin = 'testsysadmin'
        test_username = 'johndoe1'
        test_client = self.get_backwards_compatible_test_client()
        context = {'model': model, 'session': model.Session, 'user': test_sysadmin}

        # removing one member from organization
        url = h.url_for('hdx_members.member_delete', id='hdx-test-org')
        test_client.post(url, params={'user': 'johndoe1'}, extra_environ={"REMOTE_USER": test_sysadmin})

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
        ret_page = test_client.post(url, params={'organization': 'hdx-test-org', 'role': 'editor', 'save': 'save',
                                                 'message': 'add me to your organization'},
                                    extra_environ={"REMOTE_USER": test_username})
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
