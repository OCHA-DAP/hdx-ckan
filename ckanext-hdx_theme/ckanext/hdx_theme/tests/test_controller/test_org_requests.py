# -*- coding: utf-8 -*-

'''
Created on Jul 23, 2014

@author: alexandru-m-g
'''
import ckan.model as model
import logging as logging
import ckan.lib.helpers as h

import ckanext.hdx_theme.tests.hdx_test_base as hdx_test_base
import ckanext.hdx_theme.org_controller as org_controller

log = logging.getLogger(__name__)


mail_info = None
original_send_mail = None

def send_mail(recipients, subject, body):
    global mail_info
    if recipients and len(recipients) > 0:
        mail_info = u'\nSending email to {recipients} with subject "{subject}" with body: {body}' \
            .format(recipients=', '.join([r['display_name'] + ' - ' + r['email'] for r in recipients]), subject=subject, body=body)

class TestHDXReqsOrgController(hdx_test_base.HdxBaseTest):

    def setup(self):
        global original_send_mail
        original_send_mail = org_controller.send_mail
        org_controller.send_mail = send_mail

    def teardown(self):
        global original_send_mail
        global mail_info
        org_controller.send_mail = original_send_mail
        mail_info = None
        original_send_mail = None

    def test_new_org_req_email_body(self):
        global original_send_mail
        global mail_info

        assert not mail_info, 'There should be no info yet in mail_info'
        assert original_send_mail, 'original_send_mail should be already set'

        user = model.User.by_name('tester')
        user.email = 'test@test.com'
        auth = {'Authorization': str(user.apikey)}
        postparams = {
            'save': '',
            'title': 'Test org',
            'org_url': 'http://test.com',
            'description': 'Test description',
            'your_email': 'email1@testemail.com',
            'your_name': 'Test User'
        }
        offset = h.url_for(controller='ckanext.hdx_theme.org_controller:HDXReqsOrgController',
                           action='request_new_organization')
        self.app.post(offset, params=postparams,
                            extra_environ=auth)

        assert mail_info, 'This needs to contain the email that will be sent'
        assert 'tester' in mail_info, 'Ckan username needs to be in the email'
        assert 'test@test.com' in mail_info, 'Ckan email needs to be in the email'
        assert 'Test User' in mail_info, 'Person\'s name needs to be in the email'
        assert 'email1@testemail.com' in mail_info, 'Person\'s email needs to be in the email'
        assert 'Test description' in mail_info, 'Description needs to be in the email'
        assert 'Test org' in mail_info, 'Org name needs to be in the email'
        assert 'http://test.com' in mail_info, 'Org url needs to be in the email'

    def test_new_org_req_with_special_chars(self):
        global original_send_mail
        global mail_info

        assert not mail_info, 'There should be no info yet in mail_info'
        assert original_send_mail, 'original_send_mail should be already set'

        user = model.User.by_name('tester')
        auth = {'Authorization': str(user.apikey)}
        postparams = {
            'save': '',
            'title': 'Org êßȘ',
            'org_url': 'http://test.com',
            'description': 'Description ê,ß, and Ș',
            'your_email': 'email1@testemail.com',
            'your_name': 'Test êßȘ'
        }
        offset = h.url_for(controller='ckanext.hdx_theme.org_controller:HDXReqsOrgController',
                           action='request_new_organization')
        self.app.post(offset, params=postparams,
                            extra_environ=auth)

        assert mail_info, 'This needs to contain the email that will be sent'
        assert 'tester' in mail_info, 'Ckan username needs to be in the email'
        assert u'Test êßȘ' in mail_info, 'Person\'s name needs to be in the email'
        assert 'email1@testemail.com' in mail_info, 'Person\'s email needs to be in the email'
        assert u'Description ê,ß, and Ș' in mail_info, 'Description needs to be in the email'
        assert u'Org êßȘ' in mail_info, 'Org name needs to be in the email'
        assert 'http://test.com' in mail_info, 'Org url needs to be in the email'

