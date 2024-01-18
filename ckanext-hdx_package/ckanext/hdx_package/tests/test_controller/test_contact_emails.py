import mock

import ckan.model as model
import ckan.tests.factories as factories
import ckan.plugins.toolkit as tk

import ckanext.hdx_theme.tests.hdx_test_with_inds_and_orgs as hdx_test_with_inds_and_orgs

url_for = tk.url_for

class TestContactEmails(hdx_test_with_inds_and_orgs.HDXWithIndsAndOrgsTest):

    @mock.patch('ckanext.hdx_package.actions.get.hdx_mailer.mail_recipient')
    def test_contact_members(self, mocked_mail_recipient):
        member = model.User.by_name('tester')
        member.email = 'tester@test.com'

        sysadmin = model.User.by_name('testsysadmin')
        sysadmin.email = 'testsysadmin@test.com'
        sysadmin_token = factories.APIToken(user='testsysadmin', expires_in=2, unit=60 * 60)
        auth = {'Authorization': sysadmin_token['token']}

        post_params = {
            'source_type': 'dataset',
            'title': 'Test page title',
            'org_id': 'hdx-test-org',
            'pkg_id': 'test_dataset_1',
            'topic': 'all',
            'fullname': 'Sender Name',
            'email': 'sender_email@test.com',
            'msg': 'This is a test message'
        }

        url = url_for('hdx_contact.contact_members')

        res = self.app.post(url, params=post_params,
                            extra_environ=auth)

        assert '{"success": true}' in res.body

        args, kw_args = mocked_mail_recipient.call_args

        assert len(args[0]) == 2, 'mail goes to sender, org admin'
        assert post_params['msg'] in args[2].get('msg')
        assert kw_args.get('sender_name') == post_params['fullname']
        assert kw_args.get('sender_email') == post_params['email']
        assert 'email/content/group_message.html' == kw_args.get('snippet')
