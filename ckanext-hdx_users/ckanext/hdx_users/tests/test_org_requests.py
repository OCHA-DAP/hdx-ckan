# -*- coding: utf-8 -*-

'''
Created on Jul 23, 2014

@author: alexandru-m-g
'''
import mock
import ckan.model as model
import logging as logging
import ckan.lib.helpers as h

import ckanext.hdx_theme.tests.hdx_test_base as hdx_test_base
import ckanext.hdx_theme.util.mail as hdx_mail
import ckanext.hdx_org_group.tests as org_group_base
import ckanext.hdx_users.actions.misc as hdx_new_mail

from ckanext.hdx_org_group.helpers.static_lists import ORGANIZATION_TYPE_LIST

log = logging.getLogger(__name__)

mail_info = None
original_send_mail = None


def send_mail(recipients, subject, body):
    global mail_info
    if recipients and len(recipients) > 0:
        mail_info = u'\nSending email to {recipients} with subject "{subject}" with body: {body}' \
            .format(recipients=', '.join([r['display_name'] + ' - ' + r['email'] for r in recipients]), subject=subject,
                    body=body)


class TestHDXReqsOrgController(org_group_base.OrgGroupBaseTest):

    @classmethod
    def _load_plugins(cls):
        hdx_test_base.load_plugin('ytp_request hdx_org_group hdx_theme')

    def setup(self):
        global original_send_mail
        original_send_mail = hdx_mail.send_mail
        hdx_mail.send_mail = send_mail


    def teardown(self):
        global original_send_mail
        global mail_info
        hdx_mail.send_mail = original_send_mail
        mail_info = None
        original_send_mail = None

    @mock.patch('ckanext.hdx_package.actions.get.hdx_mailer.mail_recipient')
    def test_new_org_req_email_body(self, mocked_mail_recipient):
        global original_send_mail
        global mail_info

        assert not mail_info, 'There should be no info yet in mail_info'
        assert original_send_mail, 'original_send_mail should be already set'

        user = model.User.by_name('tester')
        user.email = 'test@test.com'
        auth = {'Authorization': str(user.apikey)}
        postparams = {
            'save': '',
            'name': 'Test org',
            'url': 'http://test.com',
            'acronym': 'TOACRONYM',
            'org_type': ORGANIZATION_TYPE_LIST[0][1],
            'description': 'Test description',
            'description_data': 'Test description data',
            'work_email': 'emailwork1@testemail.com',
            'your_email': 'email1@testemail.com',
            'your_name': 'Test User'
        }
        # offset = h.url_for(controller='ckanext.hdx_org_group.controllers.request_controller:HDXReqsOrgController',
        #                    action='request_new_organization')
        offset = h.url_for(controller='ckanext.hdx_users.controllers.mail_validation_controller:ValidationController',
                           action='request_new_organization')
        self.app.post(offset, params=postparams, extra_environ=auth)
        args, kw_args = mocked_mail_recipient.call_args

        # assert len(args[0]) == 2, 'mail goes to sender, org admin'
        # assert post_params['msg'] in args[2].get('msg')
        # assert kw_args.get('sender_name') == post_params['fullname']
        # assert kw_args.get('sender_email') == post_params['email']
        # assert 'email/content/group_message.html' == kw_args.get('snippet')
        assert args, 'This needs to contain the email that will be sent'
        assert 'test@test.com' in args[0][0].get('email')
        assert 'Test User' in args[0][0].get('display_name')
        assert u'Confirmation of your request to create a new organisation on HDX' in args[1]
        assert 'org_name' in args[2]
        assert 'Test User' in args[2].get('user_fullname')
        assert 'email/content/new_org_request_confirmation_to_user.html' in kw_args.get('snippet')
        assert 'test@test.com' in kw_args.get('footer')
        # assert 'tester' in mail_info, 'Ckan username needs to be in the email'
        # assert 'test@test.com' in mail_info, 'Ckan email needs to be in the email'
        # assert 'Test User' in mail_info, 'Person\'s name needs to be in the email'
        # assert 'email1@testemail.com' in mail_info, 'Person\'s email needs to be in the email'
        # assert 'emailwork1@testemail.com' in mail_info, 'Person\'s work email needs to be in the email'
        # assert 'Test description' in mail_info, 'Description needs to be in the email'
        # assert 'Test description data' in mail_info, 'Description data needs to be in the email'
        # assert 'Test org' in mail_info, 'Org name needs to be in the email'
        # assert 'http://test.com' in mail_info, 'Org url needs to be in the email'
        # assert ORGANIZATION_TYPE_LIST[0][1] in mail_info, 'Org type needs to be in the email'
        # assert 'TOACRONYM' in mail_info, 'Org acronym needs to be in the email'

    @mock.patch('ckanext.hdx_package.actions.get.hdx_mailer.mail_recipient')
    def test_new_org_req_with_special_chars(self, mocked_mail_recipient):
        global original_send_mail
        global mail_info

        assert not mail_info, 'There should be no info yet in mail_info'
        assert original_send_mail, 'original_send_mail should be already set'

        user = model.User.by_name('tester')
        auth = {'Authorization': str(user.apikey)}
        postparams = {
            'save': '',
            'name': 'Org êßȘ',
            'acronym': 'SCOACRONYM',
            'org_type': ORGANIZATION_TYPE_LIST[0][1],
            'url': 'http://test.com',
            'description': 'Description ê,ß, and Ș',
            'description_data': 'Description data ê,ß, and Ș',
            'work_email': 'emailwork1@testemail.com',
            'your_email': 'email1@testemail.com',
            'your_name': 'Test êßȘ'
        }
        # offset = h.url_for(controller='ckanext.hdx_org_group.controllers.request_controller:HDXReqsOrgController',
        #                    action='request_new_organization')
        offset = h.url_for(controller='ckanext.hdx_users.controllers.mail_validation_controller:ValidationController',
                           action='request_new_organization')
        self.app.post(offset, params=postparams, extra_environ=auth)
        args0, kw_args0 = mocked_mail_recipient.call_args_list[0]
        args1, kw_args1 = mocked_mail_recipient.call_args_list[1]

        req_dict = args0[2]
        assert postparams.get('name') == str(req_dict.get('org_name'))
        assert postparams.get('acronym') == str(req_dict.get('org_acronym'))
        assert postparams.get('org_type') == str(req_dict.get('org_type'))
        assert postparams.get('url') == str(req_dict.get('org_website'))
        assert postparams.get('description') == str(req_dict.get('org_description'))
        assert postparams.get('description_data') == str(req_dict.get('data_description'))
        assert postparams.get('work_email') == str(req_dict.get('requestor_work_email'))
        assert postparams.get('your_name') == str(req_dict.get('user_fullname'))

        # assert mail_info, 'This needs to contain the email that will be sent'
        # assert 'tester' in mail_info, 'Ckan username needs to be in the email'
        # assert u'Test êßȘ' in mail_info, 'Person\'s name needs to be in the email'
        # assert 'email1@testemail.com' in mail_info, 'Person\'s email needs to be in the email'
        # assert 'emailwork1@testemail.com' in mail_info, 'Person\'s work email needs to be in the email'
        # assert u'Description ê,ß, and Ș' in mail_info, 'Description needs to be in the email'
        # assert u'Description data ê,ß, and Ș' in mail_info, 'Description data needs to be in the email'
        # assert u'Org êßȘ' in mail_info, 'Org name needs to be in the email'
        # assert 'http://test.com' in mail_info, 'Org url needs to be in the email'
        # assert ORGANIZATION_TYPE_LIST[0][1] in mail_info, 'Org type needs to be in the email'
        # assert 'SCOACRONYM' in mail_info, 'Org acronym needs to be in the email'
