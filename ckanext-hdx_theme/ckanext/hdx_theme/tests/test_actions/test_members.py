'''
Created on Jun 17, 2014

@author: alexandru-m-g
'''
import pytest
import six
import mock

import ckan.tests.legacy as tests
import ckan.plugins.toolkit as tk
import ckan.model as model

import ckanext.hdx_theme.tests.hdx_test_base as hdx_test_base

contact_form = {
    'display_name': 'Jane Doe3',
    'name': 'janedoe3',
    'fullname': 'johnfoo',
    'email': 'janedoe3@test.test',
    'organization': 'Test Organization',
    'message': 'Lorep Ipsum',
    'admins': [{'display_name': 'Admin 1', 'email': 'admin1@hdx.org'},
               {'display_name': 'Admin 1', 'email': 'admin1@hdx.org'}]
}

janedoe3 = {
    'name': 'janedoe3',
    'fullname': 'Jane Doe3',
    'email': 'janedoe3@test.test',
    'password': 'password',
    'about': 'Jane Doe3, 3rd user created by HDXWithIndsAndOrgsTest. Member of hdx-test-org.'
}


class TestMemberActions(hdx_test_base.HdxBaseTest):

    @classmethod
    def _get_action(cls, action_name):
        return tk.get_action(action_name)

    @classmethod
    def _create_test_data(cls):
        pass

    def test_member_search(self):
        admin = self._admin_create()
        assert admin
        usernames = self._users_create(admin['apikey'])
        assert usernames
        assert len(usernames) == 3

        org = self._org_create(admin['apikey'], usernames)
        assert org

        result_members1 = self._query_members_in_org(org, admin, 'bar', True)
        assert len(result_members1) == 2, 'Users: username1 and adambar should match'
        result_mem_names = [result_mem1[4] for result_mem1 in result_members1]
        assert 'adambar' in result_mem_names
        assert 'George Foobar' in result_mem_names

        # queries should be case insensitive
        result_members2 = self._query_members_in_org(org, admin, 'JOHN', False)
        assert len(result_members2) == 1, 'just johnfoo should match'
        assert len(result_members2[0]) == 4, 'the name/fullname should not be returned'

        result_members3 = self._query_members_in_org(org, admin, '', False)
        assert len(result_members3) == 4, \
            '''empty queries should return all members
            (including the admin that created the org)
            instead it returned {num}'''.format(num=len(result_members3))

        result_basic_user_info = self._query_basic_user_info(admin)
        assert u'example-admin@example.com' == result_basic_user_info.get('email')
        assert u'test123admin' == result_basic_user_info.get('display_name')
        assert 'ds_num' in result_basic_user_info
        assert 'org_num' in result_basic_user_info
        assert 'grp_num' in result_basic_user_info
        assert len(result_basic_user_info) == 9

    def _admin_create(self):
        context = {'ignore_auth': True,
                        'model': model, 'session': model.Session, 'user': 'nouser'}
        u = self._get_action('user_create')(context,
                {'name': 'test123admin', 'email': 'example-admin@example.com', 'password': 'abcdefgh'})
        user = model.Session.query(model.User).filter(model.User.id == u['id']).first()
        user.sysadmin = True
        user.apikey = 'TEST_API_KEY'
        model.Session.commit()
        context['user'] = u['name']
        ret_user =  self._get_action("user_show")(context, {'id': u['id']})
        return ret_user

    def _users_create(self, apikey):
        u1 = tests.call_action_api(self.app, 'user_create', name='johnfoo', fullname='John Foo',
                email='example@example.com', password='abcdefgh',
                apikey=apikey, status=200)
        u2 = tests.call_action_api(self.app, 'user_create', name='adambar',
                email='example2@example.com', password='abcdefgh',
                apikey=apikey, status=200)
        u3 = tests.call_action_api(self.app, 'user_create', name='username1', fullname='George Foobar',
                email='example3@example.com', password='abcdefgh',
                apikey=apikey, status=200)

        return [u1['name'], u2['name'], u3['name']]

    def _org_create(self, apikey, usernames):
        users = [{'name': name} for name in usernames]
        org = tests.call_action_api(self.app, 'organization_create', name='test-org-123',
                users=users,
                apikey=apikey, status=200)
        return org

    def _query_members_in_org(self, org, user, query, show_user_name):

        members = tests.call_action_api(self.app, 'member_list',
                              id=org['id'], object_type='user', q=query, user_info=show_user_name,
                              apikey=user['apikey'], status=200)
        return members

    def _query_basic_user_info(self, user):
        basic_info = tests.call_action_api(self.app, 'hdx_basic_user_info', id=user.get('id'), status=200,
                                           apikey=user.get('apikey'))
        return basic_info

    # @pytest.mark.skipif(six.PY3, reason=u"The hdx_org_group plugin is not available on PY3 yet")
    @mock.patch('ckanext.hdx_package.actions.get.hdx_mailer.mail_recipient')
    def test_hdx_send_editor_request_for_org(self, mocked_mail_recipient):

        context_sysadmin = {'ignore_auth': True,
                   'model': model, 'session': model.Session, 'user': 'testsysadmin'}
        user = self._get_action('user_create')(context_sysadmin, janedoe3)
        assert user

        context = {'ignore_auth': True, 'model': model, 'session': model.Session, 'user': 'janedoe3'}
        try:
            res = self._get_action('hdx_send_editor_request_for_org')(context, contact_form)
        except Exception as ex:
            assert False
        assert True
