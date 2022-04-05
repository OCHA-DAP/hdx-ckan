# -*- coding: utf-8 -*-
import logging as logging

import mock
import pytest
import six
from six import text_type
import ckan.model as model
import ckan.plugins.toolkit as tk
import ckanext.hdx_org_group.tests as org_group_base
import ckanext.hdx_theme.tests.hdx_test_base as hdx_test_base
import ckanext.hdx_theme.util.mail as hdx_mail
from ckanext.hdx_org_group.helpers.static_lists import ORGANIZATION_TYPE_LIST

log = logging.getLogger(__name__)

mail_info = None
original_send_mail = None
h = tk.h


def send_mail(recipients, subject, body):
    global mail_info
    if recipients and len(recipients) > 0:
        mail_info = u'\nSending email to {recipients} with subject "{subject}" with body: {body}' \
            .format(recipients=', '.join([r['display_name'] + ' - ' + r['email'] for r in recipients]), subject=subject,
                    body=body)


# @pytest.mark.skipif(six.PY3, reason=u'Tests not ready for Python 3')
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

        offset = h.url_for('hdx_user.request_new_organization')
        res_post = self.app.post(offset, params=postparams, extra_environ=auth)
        args, kw_args = mocked_mail_recipient.call_args

        assert args, 'This needs to contain the email that will be sent'
        assert 'test@test.com' in args[0][0].get('email')
        assert 'Test User' in args[0][0].get('display_name')
        assert u'Confirmation of your request to create a new organisation on HDX' in args[1]
        assert 'org_name' in args[2]
        assert 'Test User' in args[2].get('user_fullname')
        assert 'email/content/new_org_request_confirmation_to_user.html' in kw_args.get('snippet')
        assert 'test@test.com' in kw_args.get('footer')

    def convert_to_unicode(self, text):
        if isinstance(text, text_type):
            return text
        return text_type(text, encoding='utf8', errors='ignore')

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
        offset = h.url_for('hdx_user.request_new_organization')
        res_post = self.app.post(offset, params=postparams, extra_environ=auth)
        args0, kw_args0 = mocked_mail_recipient.call_args_list[0]
        args1, kw_args1 = mocked_mail_recipient.call_args_list[1]

        req_dict = args0[2]
        assert self.convert_to_unicode(postparams.get('name')) == req_dict.get('org_name')
        assert self.convert_to_unicode(postparams.get('acronym')) == req_dict.get('org_acronym')
        assert self.convert_to_unicode(postparams.get('org_type')) == req_dict.get('org_type')
        assert self.convert_to_unicode(postparams.get('url')) == req_dict.get('org_website')
        assert self.convert_to_unicode(postparams.get('description')) == req_dict.get('org_description')
        assert self.convert_to_unicode(postparams.get('description_data')) == req_dict.get('data_description')
        assert self.convert_to_unicode(postparams.get('work_email')) == req_dict.get('requestor_work_email')
        assert self.convert_to_unicode(postparams.get('your_name')) == req_dict.get('user_fullname')

        assert 'email/content/new_org_request_hdx_team_notification.html' in kw_args0.get('snippet')
        assert 'email/content/new_org_request_confirmation_to_user.html' in kw_args1.get('snippet')
