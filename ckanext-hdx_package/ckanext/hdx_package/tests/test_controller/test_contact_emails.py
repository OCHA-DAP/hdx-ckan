import mock

import ckan.model as model
from ckan.lib.helpers import url_for

import ckanext.hdx_theme.tests.hdx_test_with_inds_and_orgs as hdx_test_with_inds_and_orgs


class TestContactEmails(hdx_test_with_inds_and_orgs.HDXWithIndsAndOrgsTest):

    @mock.patch('ckanext.hdx_package.actions.get.hdx_mailer.mail_recipient')
    def test_contact_members(self, mocked_mail_recipient):
        user = model.User.by_name('testsysadmin')
        user.email = 'test@test.com'
        auth = {'Authorization': str(user.apikey)}

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

        url = url_for(controller='ckanext.hdx_package.controllers.dataset_controller:DatasetController',
                        action='contact_members')

        res = self.app.post(url, params=post_params,
                            extra_environ=auth)

        assert '{"success": true}' in res.body

        args, kw_args = mocked_mail_recipient.call_args

        assert len(kw_args.get('recipients_list', [])) >=2, 'mail goes to sender and at least 1 org member'
        assert post_params['msg'] in kw_args.get('body')
        assert kw_args.get('sender_name') == post_params['fullname']
        assert kw_args.get('sender_email') == post_params['email']
