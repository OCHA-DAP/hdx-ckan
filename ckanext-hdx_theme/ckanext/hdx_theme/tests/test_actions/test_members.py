'''
Created on Jun 17, 2014

@author: alexandru-m-g
'''

import ckan.tests as tests
import ckan.plugins.toolkit as tk
import ckan.model as model

import ckanext.hdx_theme.tests.hdx_test_base as hdx_test_base


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


    def _admin_create(self):
        context = {'ignore_auth': True,
                        'model': model, 'session': model.Session, 'user': 'nouser'}
        u = self._get_action('user_create')(context,
                {'name': 'test123admin', 'email': 'example-admin@example.com', 'password': 'abcd'})
        user = model.Session.query(model.User).filter(model.User.id == u['id']).first()
        user.sysadmin = True
        model.Session.commit()
        ret_user =  self._get_action("user_show")(context, {'id': u['id']})
        ret_user['apikey'] = u['apikey']
        return ret_user

    def _users_create(self, apikey):
        u1 = tests.call_action_api(self.app, 'user_create', name='johnfoo', fullname='John Foo',
                email='example@example.com', password='abcd',
                apikey=apikey, status=200)
        u2 = tests.call_action_api(self.app, 'user_create', name='adambar',
                email='example2@example.com', password='abcd',
                apikey=apikey, status=200)
        u3 = tests.call_action_api(self.app, 'user_create', name='username1', fullname='George Foobar',
                email='example3@example.com', password='abcd',
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
