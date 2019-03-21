'''
Created on March 21, 2019

@author: dan mihaila
'''

import logging as logging
import mock
import ckan.plugins.toolkit as tk
import ckanext.hdx_theme.tests.hdx_test_base as hdx_test_base

log = logging.getLogger(__name__)

contact_form = {
    'topic': 'Getting Started',
    'fullname': 'hdx',
    'email': 'hdx.feedback@gmail.com',
    'faq-mesg': 'my question',
}


class TestFaqController(hdx_test_base.HdxBaseTest):

    @classmethod
    def _get_action(cls, action_name):
        return tk.get_action(action_name)

    @mock.patch('ckanext.hdx_package.actions.get.hdx_mailer.mail_recipient')
    def test_faq_contact_us(self, mocked_mail_recipient):

        try:
            res = self.app.post('/faq/contact_us', params=contact_form)
        except Exception, ex:
            assert False
        assert '200 OK' in res.status
        assert "success" in res.body and "true" in res.body
        assert True
