'''
Created on Jun 23, 2015

@author: alexandru-m-g
'''

import logging
import mock
import ckan.model as model
import ckan.common as common
import ckan.lib.helpers as h
import ckan.lib.mailer as mailer

import ckanext.hdx_theme.tests.hdx_test_base as hdx_test_base
import ckanext.hdx_theme.tests.mock_helper as mock_helper
import ckanext.hdx_org_group.controllers.member_controller as member_controller
import ckanext.hdx_org_group.tests as org_group_base

c = common.c
log = logging.getLogger(__name__)

q = None
sort = None
c_dict = None

invited_user = None


class TestMembersController(org_group_base.OrgGroupBaseWithIndsAndOrgsTest):
    @classmethod
    def _load_plugins(cls):
        hdx_test_base.load_plugin('ytp_request hdx_org_group hdx_theme')

    @classmethod
    def _create_test_data(cls):
        super(TestMembersController, cls)._create_test_data(create_datasets=False, create_members=True)

    def setup(self):
        global q, sort, c_dict
        q = None
        sort = None
        c_dict = None
        user_invite_params = None

    def _populate_member_names(self, members, users):
        ret = [next(user['fullname'] for user in users if user['id'] == member[0]) for member in members]
        return ret

    @mock.patch('ckanext.hdx_theme.helpers.helpers.c')
    @mock.patch('ckanext.hdx_org_group.helpers.organization_helper.c')
    @mock.patch('ckanext.hdx_org_group.controllers.member_controller.c')
    def test_members(self, member_c, org_helper_c, theme_c):
        global sort, q

        test_username = 'testsysadmin'
        mock_helper.populate_mock_as_c(member_c, test_username)
        mock_helper.populate_mock_as_c(org_helper_c, test_username)
        mock_helper.populate_mock_as_c(theme_c, test_username)

        context = {
            'model': model, 'session': model.Session, 'user': 'testsysadmin'}
        org = self._get_action('organization_show')(context, {'id': 'hdx-test-org'})

        # By default the users should be sorted alphabetically asc
        user_controller = MockedHDXOrgMemberController()
        user_controller.members('hdx-test-org')
        user_list = self._populate_member_names(c_dict['members'], org['users'])

        for idx, val in enumerate(user_list):
            if idx < len(user_list) - 1 and user_list[idx] and user_list[idx + 1]:
                assert user_list[idx] < user_list[idx + 1], "{} should be before {}". \
                    format(user_list[idx], user_list[idx + 1])

        # Sorting alphabetically desc
        sort = 'title desc'
        user_controller.members('hdx-test-org')
        user_list = self._populate_member_names(c_dict['members'], org['users'])

        for idx, val in enumerate(user_list):
            if idx < len(user_list) - 1 and user_list[idx] and user_list[idx + 1]:
                assert user_list[idx] > user_list[idx + 1], "{} should be before {}". \
                    format(user_list[idx], user_list[idx + 1])

        # Sorting alphabetically desc
        q = 'anna'
        user_controller.members('hdx-test-org')
        user_list = self._populate_member_names(c_dict['members'], org['users'])

        assert len(user_list) == 1, "Only one user should be found for query"
        assert user_list[0] == 'Anna Anderson2'

    @mock.patch('ckanext.hdx_theme.helpers.helpers.c')
    @mock.patch('ckanext.hdx_org_group.helpers.organization_helper.c')
    @mock.patch('ckanext.hdx_org_group.controllers.member_controller.c')
    def test_members_delete_add(self, member_c, org_helper_c, theme_c):
        test_username = 'testsysadmin'
        mock_helper.populate_mock_as_c(member_c, test_username)
        mock_helper.populate_mock_as_c(org_helper_c, test_username)
        mock_helper.populate_mock_as_c(theme_c, test_username)

        url = h.url_for(
            controller='ckanext.hdx_org_group.controllers.member_controller:HDXOrgMemberController',
            action='member_delete',
            id='hdx-test-org'
        )
        self.app.post(url, params={'user': 'annaanderson2'}, extra_environ={"REMOTE_USER": "testsysadmin"})

        context = {
            'model': model, 'session': model.Session, 'user': 'testsysadmin'}
        org = self._get_action('organization_show')(context, {'id': 'hdx-test-org'})

        user_controller = MockedHDXOrgMemberController()
        user_controller.members('hdx-test-org')
        user_list = self._populate_member_names(c_dict['members'], org['users'])

        deleted_length = len(user_list)
        assert 'Anna Anderson2' not in user_list

        url = h.url_for(
            controller='ckanext.hdx_org_group.controllers.member_controller:HDXOrgMemberController',
            action='member_new',
            id='hdx-test-org'
        )
        self.app.post(url, params={'username': 'annaanderson2', 'role': 'editor'},
                      extra_environ={"REMOTE_USER": "testsysadmin"})
        org = self._get_action('organization_show')(context, {'id': 'hdx-test-org'})

        assert len(org['users']) == deleted_length + 1, 'Number of members should have increased by 1'

        member_anna = next((user for user in org['users'] if user['name'] == 'annaanderson2'), None)
        assert member_anna, 'User annaanderson2 needs to be a member of the org'
        assert member_anna['capacity'] == 'editor', 'User annaanderson2 needs to be an editor'

    def test_members_invite(self):

        original_send_invite = mailer.send_invite

        def mock_send_invite(user):
            global invited_user
            invited_user = user

        mailer.send_invite = mock_send_invite

        context = {
            'model': model, 'session': model.Session, 'user': 'testsysadmin'}
        url = h.url_for(
            controller='ckanext.hdx_org_group.controllers.member_controller:HDXOrgMemberController',
            action='member_new',
            id='hdx-test-org'
        )
        self.app.post(url, params={'email': 'hdxtestuser123@test.test', 'role': 'editor'},
                      extra_environ={"REMOTE_USER": "testsysadmin"})
        org = self._get_action('organization_show')(context, {'id': 'hdx-test-org'})

        new_member = next((user for user in org['users'] if 'hdxtestuser123' in user['name']), None)
        assert new_member, 'Invited user needs to be a member of the org'
        assert new_member['capacity'] == 'editor', 'Invited user needs to be an editor'

        mailer.send_invite = original_send_invite

    @mock.patch('ckanext.hdx_theme.helpers.helpers.c')
    @mock.patch('ckanext.hdx_org_group.helpers.organization_helper.c')
    @mock.patch('ckanext.hdx_org_group.controllers.member_controller.c')
    def test_bulk_members_invite(self, member_c, org_helper_c, theme_c):
        test_username = 'testsysadmin'
        mock_helper.populate_mock_as_c(member_c, test_username)
        mock_helper.populate_mock_as_c(org_helper_c, test_username)
        mock_helper.populate_mock_as_c(theme_c, test_username)
        original_send_invite = mailer.send_invite

        def mock_send_invite(user):
            global invited_user
            invited_user = user

        mailer.send_invite = mock_send_invite
        context = {'model': model, 'session': model.Session, 'user': test_username}

        # removing one member from organization
        url = h.url_for(
            controller='ckanext.hdx_org_group.controllers.member_controller:HDXOrgMemberController',
            action='member_delete',
            id='hdx-test-org'
        )
        self.app.post(url, params={'user': 'johndoe1'}, extra_environ={"REMOTE_USER": test_username})

        org = self._get_action('organization_show')(context, {'id': 'hdx-test-org'})
        user_controller = MockedHDXOrgMemberController()
        user_controller.members('hdx-test-org')
        user_list = self._populate_member_names(c_dict['members'], org['users'])
        deleted_length = len(user_list)
        assert 'John Doe1' not in user_list

        # bulk adding members
        url = h.url_for(
            controller='ckanext.hdx_org_group.controllers.member_controller:HDXOrgMemberController',
            action='bulk_member_new',
            id='hdx-test-org'
        )

        self.app.post(url, params={'emails': 'janedoe3,johndoe1,dan@k.ro', 'role': 'editor'},
                      extra_environ={"REMOTE_USER": test_username})
        org = self._get_action('organization_show')(context, {'id': 'hdx-test-org'})

        assert len(org['users']) == deleted_length + 2, 'Number of members should have increased by 2'
        new_member = next((user for user in org['users'] if 'johndoe1' in user['name']), None)
        assert new_member, 'Invited user needs to be a member of the org'
        assert new_member['capacity'] == 'editor', 'Invited user needs to be an editor'

        # making john doe1 a member back
        self.app.post(url, params={'emails': 'johndoe1', 'role': 'member'},
                      extra_environ={"REMOTE_USER": test_username})
        org = self._get_action('organization_show')(context, {'id': 'hdx-test-org'})
        new_member = next((user for user in org['users'] if 'johndoe1' in user['name']), None)
        assert new_member, 'Invited user needs to be a member of the org'
        assert new_member['capacity'] == 'member', 'Invited user needs to be an member'

        mailer.send_invite = original_send_invite


class MockedHDXOrgMemberController(member_controller.HDXOrgMemberController):
    def _find_filter_params(self):
        return q, sort

    def _set_c_params(self, params):
        global c_dict
        c_dict = params

    def _get_context(self):
        context = {'model': model, 'session': model.Session,
                   'user': 'testsysadmin'}
        return context

    def _render_template(self, template_name):
        pass
