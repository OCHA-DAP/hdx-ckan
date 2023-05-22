'''
Created on Jul 25, 2014

@author: alexandru-m-g
'''
import logging as logging
import ckan.model as model
import ckan.tests.legacy as tests

import ckanext.hdx_theme.tests.hdx_test_base as hdx_test_base

log = logging.getLogger(__name__)


class TestUserAuth(hdx_test_base.HdxBaseTest):
    def test_access_to_user_emails(self):
        testsysadmin = model.User.by_name('testsysadmin')
        user = model.User.by_name('tester')
        user2 = model.User.by_name('annafan')
        user.email = 'test@testemail.com'

        users = tests.call_action_api(self.app, 'user_list', q='tester',
                                      apikey=testsysadmin.apikey, status=200)
        assert len(users) == 1
        assert users[0].get('email', None), "testsysadmin shoud be able to see user's email"

        users = tests.call_action_api(self.app, 'user_list', q='tester',
                                      apikey=user2.apikey, status=403)
        assert True, "user2 shoudn't be able to see user's email"

    def test_access_to_user_list(self):
        testsysadmin = model.User.by_name('testsysadmin')
        user = model.User.by_name('tester')
        user2 = model.User.by_name('annafan')

        users = tests.call_action_api(self.app, 'user_list', q='annafan', apikey=testsysadmin.apikey, status=200)

        assert len(users) == 1, 'testsysadmin should be able to see user list'

        users = tests.call_action_api(self.app, 'user_list', q='annafan', apikey=user.apikey, status=200)

        assert len(users) == 1, 'tester should be able to see user list'

        users = tests.call_action_api(self.app, 'user_list', status=403)

        assert True, 'visitor shouldn\'t be able to see user list'

    def test_access_to_user_show(self):
        testsysadmin = model.User.by_name('testsysadmin')
        user = model.User.by_name('tester')
        user.fullname = 'Test Sysadmin'

        user_show = tests.call_action_api(self.app, 'user_show', id=user.id, apikey=testsysadmin.apikey, status=200)

        assert user_show.get('fullname', None), 'testsysadmin should be able to see user fullname'

        user_show = tests.call_action_api(self.app, 'user_show', id=user.id, status=403)

        assert True, 'visitor shouldn\'t be able to see user fullname'
