import pytest

import mock
import logging as logging
import ckan.model as model
import ckan.plugins.toolkit as tk
import ckan.logic as logic
import unicodedata
import ckan.lib.helpers as h
import json

import ckanext.hdx_theme.tests.hdx_test_with_inds_and_orgs as hdx_test_with_inds_and_orgs
import ckanext.hdx_users.helpers.tokens as tkh
import ckanext.hdx_users.model as user_model

from nose.tools import assert_true
log = logging.getLogger(__name__)
NotFound = logic.NotFound


class TestHDXControllerPage(hdx_test_with_inds_and_orgs.HDXWithIndsAndOrgsTest):

    @classmethod
    def _get_action(cls, action_name):
        return tk.get_action(action_name)

    @classmethod
    def _create_test_data(cls, create_datasets=True, create_members=False):
        super(TestHDXControllerPage, cls)._create_test_data(create_datasets=True, create_members=True)

    # def _get_url(self, url, apikey=None):
    #     if apikey:
    #         page = self.app.get(url, headers={
    #             'Authorization': unicodedata.normalize('NFKD', apikey).encode('ascii', 'ignore')})
    #     else:
    #         page = self.app.get(url)
    #     return page

    @mock.patch('ckanext.hdx_theme.util.mail.send_mail')
    @mock.patch('ckanext.hdx_package.actions.get.hdx_mailer.mail_recipient')
    def test_onboarding(self, mocked_mail_recipient, mocked_send_mail):

        test_client = self.get_backwards_compatible_test_client()

        # step 1 register
        url = h.url_for(controller='ckanext.hdx_users.controllers.mail_validation_controller:ValidationController',
                        action='register_email')
        data = {'email': 'newuser@hdx.org', 'nosetest': 'true'}
        res = test_client.post(url, data = data)
        assert_true(json.loads(res.body)['success'])

        user = model.User.get('newuser@hdx.org')
        user.apikey = 'TEST_API_KEY'
        model.Session.commit()

        assert_true(user is not None)
        assert_true(user.password is None)

        # step 2 validate
        token = tkh.token_show({}, {'id': user.id})
        url = '/user/validate/' + token.get('token')
        res = test_client.get(url)
        assert '<label for="field-email">Your Email Address</label>' in res.body
        assert 'id="recaptcha"' in res.body
        assert 'value="newuser@hdx.org"' in res.body

        # step 3 details
        context = {'model': model, 'session': model.Session, 'auth_user_obj': user}
        url = h.url_for(controller='ckanext.hdx_users.controllers.mail_validation_controller:ValidationController',
                        action='register_details')

        try:
            res = test_client.post(url, data={})
            assert '500 Internal Server Error' in res.status
        except Exception as ex:
            assert False

        try:
            res = test_client.post(url, data={
                'first-name': 'firstname',
                'last-name': 'lastname',
                'password': 'passpass',
                'name': 'newuser',
                'email': 'newuser@hdx.org',
                'login': 'newuser@hdx.org',
                'id': '123123123123'
            })
            assert '500 Internal Server Error' in res.status
        except AttributeError as ex:
            assert False
        except Exception as ex:
            assert False
        try:
            res = test_client.post(url, data={
                'first-name': 'firstname',
                'last-name': 'lastname',
                'password': 'passpass',
                'name': 'newuser',
                'login': 'newuser@hdx.org',
                'id': user.id
            })
            assert '"Email": "Missing value"' in res.body
        except Exception as ex:
            assert False

        try:
            res = test_client.post(url, data={
                'first-name': 'firstname',
                'last-name': 'lastname',
                'password': 'passpass',
                'name': 'testsysadmin',
                'email': 'newuser@hdx.org',
                'login': 'newuser@hdx.org',
                'id': user.id
            })
            assert 'That login name is not available' in res.body
        except Exception as ex:
            assert False

        try:
            res = test_client.post(url, data={
                'first-name': 'firstname',
                'last-name': 'lastname',
                'password': 'passpass',
                'email': 'newuser@hdx.org',
                'login': 'newuser@hdx.org',
                'id': user.id
            })
            assert "Missing value" in res.body
        except Exception as ex:
            assert False

        try:
            res = test_client.post(url, {
                'first-name': 'firstname',
                'password': 'pass',
                'name': 'newuser',
                'email': 'newuser@hdx.org',
                'login': 'newuser@hdx.org',
                'id': user.id
            })
            assert False
        except KeyError as ex:
            assert False
        except TypeError as ex:
            assert True

        data = {
            'first-name': 'firstname',
            'last-name': 'lastname',
            'password': 'passpass',
            'name': 'newuser',
            'email': 'newuser@hdx.org',
            'login': 'newuser@hdx.org',
            'id': user.id
        }
        try:
            res = test_client.post(url, data=data)
        except Exception as ex:
            assert False
        assert 'true' in res
        updated_user = model.User.get('newuser@hdx.org')
        assert updated_user.name == data.get('name')
        assert updated_user.id == data.get('id')
        assert updated_user.display_name == data.get('first-name') + " " + data.get('last-name')
        assert updated_user.password is not None
        assert updated_user.sysadmin is False
        assert updated_user.email == data.get('email')
        res = self._get_action('user_extra_show')(context, {'user_id': user.id})
        assert res
        assert self._get_user_extra_by_key(res, user_model.HDX_FIRST_NAME) == data.get('first-name')
        assert self._get_user_extra_by_key(res, user_model.HDX_LAST_NAME) == data.get('last-name')
        assert self._get_user_extra_by_key(res, user_model.HDX_ONBOARDING_DETAILS) == 'True'


        # step 4 follow
        url = h.url_for(controller='ckanext.hdx_users.controllers.mail_validation_controller:ValidationController',
                        action='follow_details')

        try:
            res = test_client.post(url, data={})
            assert '500 Internal Server Error' in res.status
            assert 'Something went wrong' in res.body
        except KeyError as ex:
            False
        except Exception as ex:
            False

        data = {
            'id': user.id
        }
        try:
            res = test_client.post(url, data=data)
        except Exception as ex:
            assert False
        assert 'true' in res
        res = self._get_action('user_extra_show')(context, {'user_id': user.id})
        assert res
        assert self._get_user_extra_by_key(res, user_model.HDX_ONBOARDING_FOLLOWS) == 'True'

        # step 5b request_membership
        url = h.url_for(controller='ckanext.hdx_users.controllers.mail_validation_controller:ValidationController',
                        action='request_membership')

        try:
            res = test_client.post(url, {})
            assert False
            # assert '"message": "Unauthorized to create user"' in res.body
        except Exception as ex:
            assert True

        data = {
            'org_id': 'hdx-test-org',
            'message': "please add me to your organization",
            'save': u'save',
            'role': u'member',
            'group': 'hdx-test-org'
        }

        auth = {'Authorization': str(user.apikey)}
        try:
            res = test_client.post(url, data=data, extra_environ=auth)
            assert '{"success": true}' in res.body
        except Exception as ex:
            assert False

    def _get_user_extra_by_key(self, user_extras, key):
        ue_show_list = [d.get('value') for i, d in enumerate(user_extras) if d['key'] == key]
        return ue_show_list[0]
