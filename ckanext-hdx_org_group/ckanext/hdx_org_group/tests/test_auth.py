'''
Created on Jul 24, 2014

@author: alexandru-m-g
'''
import datetime
import logging as logging

import ckan.lib.helpers as h
import ckan.model as model
import ckan.plugins.toolkit as tk
import ckan.tests.factories as factories
import ckan.tests.helpers as helpers

import ckanext.hdx_org_group.tests as org_group_base
import ckanext.hdx_theme.tests.hdx_test_base as hdx_test_base

from ckanext.hdx_org_group.helpers.static_lists import ORGANIZATION_TYPE_LIST
from ckanext.hdx_org_group.tests.test_data_completeness import _generate_dataset_dict

log = logging.getLogger(__name__)
_get_action = tk.get_action

class TestOrgAuth(org_group_base.OrgGroupBaseTest):

    @classmethod
    def _get_action(cls, action_name):
        return _get_action(action_name)

    @classmethod
    def _create_org(cls, username, name, title):
        org = cls._get_action('organization_create')(
            {'user': username, 'model': model, 'session': model.Session},
            {
                'name': name,
                'title': title,
                'description': 'Test Org  Description',
                'hdx_org_type': ORGANIZATION_TYPE_LIST[0][1],
                'org_url': 'https://hdx.hdxtest.org/'
            }
        )
        return org

    def test_create_org(self):
        try:
            self._create_org('tester', 'test_org_a', 'Test Org A')
            assert False, 'user should not be allowed to create an org'
        except tk.NotAuthorized:
            assert True, 'user should not be allowed to create an org'

        try:
            self._create_org('testsysadmin', 'test_org_a_admin', 'Test Org A Admin')
            assert True, 'sysadmin should be allowed to create an org'
        except tk.NotAuthorized:
            assert False, 'sysadmin should be allowed to create an org'

    def test_edit_org(self):
        create_result = self._create_org('testsysadmin', 'test_org_b', 'Test Org B')

        try:
            self._get_action('organization_update')(
                {'user': 'tester', 'model': model, 'session': model.Session},
                {'id': create_result['id'], 'title': 'Test Org B CHANGED'}
            )
            assert False, 'user should not be allowed to modify the org'
        except tk.NotAuthorized:
            assert True, 'user should not be allowed to modify the org'

    def test_delete_org(self):
        create_result = self._create_org('testsysadmin', 'test_org_c', 'Test Org C')

        try:
            self._get_action('organization_delete')(
                {'user': 'tester', 'model': model, 'session': model.Session},
                {'id': create_result['id']}
            )
            assert False, 'user should not be allowed to delete the org'
        except tk.NotAuthorized:
            assert True, 'user should not be allowed to delete the org'

    def test_create_org_member(self):
        create_result = self._create_org('testsysadmin', 'test_org_d', 'Test Org D')

        try:
            self._get_action('organization_member_create')(
                {'user': 'tester', 'model': model, 'session': model.Session},
                {'id': create_result['id'], 'username': 'tester', 'role': 'editor'}
            )
            assert False, 'user should not be allowed to add themself as a member'
        except tk.NotAuthorized:
            assert True, 'user should not be allowed to add themself as a member'


    def test_remove_self_org_member(self):
        create_result = self._create_org('testsysadmin', 'test_org_e', 'Test Org E')

        self._get_action('organization_member_create')(
            {'user': 'testsysadmin', 'model': model, 'session': model.Session},
            {'id': create_result['id'], 'username': 'annafan', 'role': 'member'}
        )

        for role in ('editor', 'member'):

            self._get_action('organization_member_create')(
                {'user': 'testsysadmin', 'model': model, 'session': model.Session},
                {'id': create_result['id'], 'username': 'tester', 'role': role}
            )

            try:
                self._get_action('organization_member_delete')(
                    {'user': 'tester', 'model': model, 'session': model.Session},
                    {'id': create_result['id'], 'username': 'annafan'}
                )
                assert False, 'a {} shouldn\'t be able to remove any other member from the org'.format(role)
            except tk.NotAuthorized:
                assert True, 'a {} shouldn\'t be able to remove any other member from the org'.format(role)

            self._get_action('organization_member_delete')(
                {'user': 'tester', 'model': model, 'session': model.Session},
                {'id': create_result['id'], 'username': 'tester'}
            )
            assert True, 'any member should be able to remove himself from an org'

        self._get_action('organization_member_create')(
            {'user': 'testsysadmin', 'model': model, 'session': model.Session},
            {'id': create_result['id'], 'username': 'tester', 'role': 'admin'}
        )

        self._get_action('organization_member_delete')(
            {'user': 'tester', 'model': model, 'session': model.Session},
            {'id': create_result['id'], 'username': 'annafan'}
        )
        assert True, 'an admin should be able to remove any other member from the org'

        self._get_action('organization_member_delete')(
            {'user': 'tester', 'model': model, 'session': model.Session},
            {'id': create_result['id'], 'username': 'tester'}
        )

        assert True, 'an admin should be able to remove himself from an org'

    def test_maintainer_protection(self):
        user = model.User.by_name('tester')

        create_result = self._create_org('testsysadmin', 'test_org_maintainer', 'Test Org Maintainer')

        # add 'tester' as an editor to the org
        self._get_action('organization_member_create')(
            {'user': 'testsysadmin', 'model': model, 'session': model.Session},
            {'id': create_result['id'], 'username': 'tester', 'role': 'editor'}
        )

        group = factories.Group(name='some_location')
        dataset = _generate_dataset_dict('dataset-maintainer1', 'test_org_maintainer', group.get('name'), datetime.datetime.utcnow(), user.id, True)

        # try to delete a member that is also a dataset maintainer from the org
        try:
            self._get_action('organization_member_delete')(
                {'user': 'testsysadmin', 'model': model, 'session': model.Session},
                {'id': create_result['id'], 'username': 'tester'}
            )
            assert False, 'an admin should not be able to remove member if maintainer of a dataset belonging to current org'
        except Exception:
            assert True, 'an admin should not be able to remove member if maintainer of a dataset belonging to current org'

        # try to change a maintainer's role to member
        try:
            self._get_action('organization_member_update')(
                {'user': 'testsysadmin', 'model': model, 'session': model.Session},
                {'id': create_result['id'], 'username': 'tester', 'role': 'member'}
            )
            assert False, 'an admin should not be able to change role to member if user is maintainer of a dataset belonging to current org'
        except Exception:
            assert True, 'an admin should not be able to change role to member if user is maintainer of a dataset belonging to current org'

        #remove dataset
        helpers.call_action(
            "package_delete", context={"user": 'testsysadmin'}, **dataset
        )

        self._get_action('organization_member_delete')(
            {'user': 'testsysadmin', 'model': model, 'session': model.Session},
            {'id': create_result['id'], 'username': 'tester'}
        )
        assert True, 'an admin should be able to remove member if not maintainer'

    def test_new_org_request_page(self):
        offset = h.url_for('hdx_org.request_new')
        result = self.app.get(offset)
        assert result.status_code == 403
        assert 'You don\'t have permission to access this page' in result.body

    def test_new_org_request(self):
        try:
            self._get_action('hdx_send_new_org_request')(
                {'model': model, 'session': model.Session},
                {'title': 'Org Title', 'description': 'Org Description',
                 'org_url': 'https://test-org.com/',
                 'your_name': 'Some Name', 'your_email': 'test@test.com'}
            )
            assert False, 'anon user should not be allowed to send new org request'
        except tk.NotAuthorized:
            assert True, 'anon user should not be allowed to send new org request'

    def test_editor_request_for_org(self):
        try:
            self._get_action('hdx_send_editor_request_for_org')(
                {'model': model, 'session': model.Session},
                {'display_name': 'User Name', 'name': 'username',
                 'email': 'test@test.com',
                 'organization': 'Org Name', 'message': 'Some message',
                 'admins': []}
            )
            assert False
        except tk.NotAuthorized:
            assert True


    # TODO need to align with the new membership request YTP extension
    # def test_request_membership(self):
    #     tests.call_action_api(self.app, 'hdx_send_request_membership',
    #                        display_name='User Name', name='username',
    #                        email='test@test.com',
    #                        organization='Org Name', message='Some message',
    #                        admins=[],
    #                        status=403)

class TestGroupAuth(org_group_base.OrgGroupBaseTest):

    @classmethod
    def _get_action(cls, action_name):
        return _get_action(action_name)

    @classmethod
    def _create_group(cls, username, name, title):
        group = cls._get_action('group_create')(
            {'user': username, 'model': model, 'session': model.Session},
            {
                'name': name,
                'title': title,
                'description': 'Test Group Description',
            }
        )
        return group

    def test_create_country(self):
        try:
            self._create_group('tester', 'test_group_a', 'Test Group A')
            assert False, 'user should not be allowed to create a group'
        except tk.NotAuthorized:
            assert True, 'user should not be allowed to create a group'

    def test_edit_country(self):
        create_result = self._create_group('testsysadmin', 'test_group_b', 'Test Group B')

        try:
            self._get_action('group_update')(
                {'user': 'tester', 'model': model, 'session': model.Session},
                {'id': create_result['id'], 'title': 'Test Group B CHANGED'}
            )
            assert False, 'user should not be allowed to modify the group'
        except tk.NotAuthorized:
            assert True, 'user should not be allowed to modify the group'

    def test_delete_country(self):
        create_result = self._create_group('testsysadmin', 'test_group_c', 'Test Group C')

        try:
            self._get_action('group_delete')(
                {'user': 'tester', 'model': model, 'session': model.Session},
                {'id': create_result['id']}
            )
            assert False, 'user should not be allowed to delete the group'
        except tk.NotAuthorized:
            assert True, 'user should not be allowed to delete the group'

    def test_create_country_member(self):
        create_result = self._create_group('testsysadmin', 'test_group_d', 'Test Group D')

        try:
            self._get_action('group_member_create')(
                {'user': 'tester', 'model': model, 'session': model.Session},
                {'id': create_result['id'], 'username': 'tester', 'role': 'editor'}
            )
            assert False, 'Country members shouldn\'t be allowed'
        except tk.NotAuthorized:
            assert True, 'Country members shouldn\'t be allowed'
