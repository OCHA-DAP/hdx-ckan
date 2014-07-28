'''
Created on Jul 25, 2014

@author: alexandru-m-g
'''
import logging as logging
import ckan.model as model
import ckan.tests as tests

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
                                      apikey=user2.apikey, status=200)
        assert len(users) == 1
        assert not users[0].get('email', None), "user2 shoudn't be able to see user's email"
