'''
Created on March 21, 2019

@author: dan mihaila
'''

import unicodedata
import logging as logging
import mock
import ckan.model as model
import ckan.lib.helpers as h
import ckan.plugins.toolkit as tk

import ckanext.hdx_theme.tests.hdx_test_base as hdx_test_base
import ckanext.hdx_theme.tests.hdx_test_with_inds_and_orgs as hdx_test_with_inds_and_orgs

log = logging.getLogger(__name__)

contact_form = {
    'topic': 'Getting Started',
    'fullname': 'hdx',
    'email': 'hdx.feedback@gmail.com',
    'faq-mesg': 'my question',
}

class TestFaqController(hdx_test_base.HdxBaseTest):

    # @classmethod
    # def _load_plugins(cls):
    #     try:
    #         # hdx_pages hdx_package hdx_search hdx_org_group
    #         hdx_test_base.load_plugin('ytp_request hdx_org_group hdx_theme')
    #     except Exception as e:
    #         log.warn('Module already loaded')
    #         log.info(str(e))

    @classmethod
    def _get_action(cls, action_name):
        return tk.get_action(action_name)

    @mock.patch('ckanext.hdx_package.actions.get.hdx_mailer.mail_recipient')
    def test_faq_contact_us(self, mocked_mail_recipient):
        # context = {'model': model, 'session': model.Session, 'user': 'tester'}
        # context_sysadmin = {'model': model, 'session': model.Session, 'user': 'testsysadmin'}

        # user = model.User.by_name('tester')
        # user.email = 'test@test.com'
        # auth = {'Authorization': str(user.apikey)}

        # post_params = self._get_page_post_param()

        try:
            res = self.app.post('/faq/contact_us', params=contact_form)
        except Exception, ex:
            assert False
        assert '200 OK' in res.status
        assert "success" in res.body and "true" in res.body
        assert True






