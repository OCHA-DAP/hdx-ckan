'''
Created on Jul 25, 2014

@author: alexandru-m-g
'''
import pytest
import mock

import logging as logging
import ckan.model as model
import ckan.plugins.toolkit as tk

import ckanext.hdx_theme.tests.hdx_test_base as hdx_test_base

log = logging.getLogger(__name__)
_get_action = tk.get_action


@pytest.mark.ckan_config('ckan.auth.public_user_details', False)
class TestUserAuth(hdx_test_base.HdxBaseTest):
    def test_access_to_user_emails_as_sysadmin(self):
        testsysadmin = model.User.by_name('testsysadmin')
        user = model.User.by_name('tester')
        user.email = 'test@testemail.com'

        users = _get_action('user_list')(
            {'user': testsysadmin.name, 'model': model, 'session': model.Session},
            {'q': 'tester'}
        )

        assert len(users) == 1
        assert users[0].get('email', None), "testsysadmin shoud be able to see user's email"

    @mock.patch('flask_login.utils._get_user')
    def test_access_to_user_emails_as_normal_user(self, current_user):
        user2 = model.User.by_name('annafan')
        current_user.return_value = user2
        users = _get_action('user_list')(
            {'user': user2.name, 'model': model, 'session': model.Session},
            {'q': 'tester'}
        )
        assert len(users) == 1
        assert not users[0].get('email'), "user2 shoudn't be able to see user's email"

    @mock.patch('flask_login.utils._get_user')
    def test_access_to_user_list_logged_in(self, current_user):
        testsysadmin = model.User.by_name('testsysadmin')
        user = model.User.by_name('tester')
        # user2 = model.User.by_name('annafan')

        users = _get_action('user_list')(
            {'user': testsysadmin.name, 'model': model, 'session': model.Session},
            {'q': 'annafan'}
        )

        assert len(users) == 1, 'testsysadmin should be able to see user list'
        current_user.return_value = user
        users = _get_action('user_list')(
            {'user': user.name, 'model': model, 'session': model.Session},
            {'q': 'annafan'}
        )

        assert len(users) == 1, 'tester should be able to see user list'

    @mock.patch('flask_login.utils._get_user')
    def test_access_to_user_list_as_anon(self, current_user):
        current_user.return_value = mock.Mock(is_anonymous=True)
        try:
            _get_action('user_list')(
                {'model': model, 'session': model.Session},
                {}
            )
            assert False, 'visitor shouldn\'t be able to see user list'
        except tk.NotAuthorized as e:
            assert True, 'visitor shouldn\'t be able to see user list'


    def test_access_to_user_show_as_sysadmin(self):
        testsysadmin = model.User.by_name('testsysadmin')
        user = model.User.by_name('tester')
        user.fullname = 'Test Sysadmin'

        user_show = _get_action('user_show')(
            {'user': testsysadmin.name, 'model': model, 'session': model.Session},
            {'id': user.id}
        )
        assert user_show.get('fullname', None), 'testsysadmin should be able to see user fullname'

    @mock.patch('flask_login.utils._get_user')
    def test_access_to_user_show_as_anon(self, current_user):
        user = model.User.by_name('tester')
        current_user.return_value = mock.Mock(is_anonymous=True)
        try:
            user_show = _get_action('user_show')(
                {'model': model, 'session': model.Session},
                {'id': user.id}
            )
            assert not user_show.get('fullname'), 'visitor shouldn\'t be able to see user fullname'
        except tk.NotAuthorized as e:
            assert True, 'visitor shouldn\'t be able to see user fullname'

