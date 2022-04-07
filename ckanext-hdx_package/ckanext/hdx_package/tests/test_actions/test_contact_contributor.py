import pytest
import mock
import six

import ckan.plugins.toolkit as toolkit
import ckan.model as model
import ckan.tests.factories as factories

import ckanext.hdx_theme.tests.hdx_test_with_inds_and_orgs as hdx_test_with_inds_and_orgs
import ckanext.hdx_theme.tests.hdx_test_base as hdx_test_base


class TestContactContributor(hdx_test_with_inds_and_orgs.HDXWithIndsAndOrgsTest):

    @classmethod
    def _load_plugins(cls):
        hdx_test_base.load_plugin('')

    @classmethod
    def setup_class(cls):
        super(TestContactContributor, cls).setup_class()
        user = model.User.by_name('testsysadmin')
        user.email = 'test@test.com'
        model.Session.commit()

    @mock.patch('ckanext.hdx_package.actions.get.hdx_mailer.mail_recipient')
    def test_hdx_send_mail_contributor(self, mocked_mail_recipient):
        data_dict = {
            "hdx_email": "hdx@test.test",
            "topic": "asked about metadata",
            "pkg_id": "test_dataset_1",
            "pkg_owner_org": "hdx-test-org",
            "pkg_url": "http://data.humdata.local/dataset/test_dataset_1",
            "msg": "This is a test",
            "fullname": "Some User",
            "pkg_title": "Testing dataset freq",
            "email": "some.user@gmail.com"
        }

        try:
            self._get_action('hdx_send_mail_contributor')({}, data_dict)
        except toolkit.NotAuthorized as e:
            assert True, 'Calling hdx_send_mail_contributor without user should raise NotAuthorized'
        except Exception as e:
            assert False, 'Calling hdx_send_mail_contributor without user should raise NotAuthorized and not {}'.format(
                type(e).__name__)

        normal_user = factories.User()
        context = {
            'model': model,
            'session': model.Session,
            'user': normal_user['name']
        }

        self._get_action('hdx_send_mail_contributor')(context, data_dict)

        assert len(mocked_mail_recipient.call_args_list) == 2, '2 separate emails should be sent'

        args0, kw_args0 = mocked_mail_recipient.call_args_list[0]
        first_email_addresses = [args0[0][0].get('email')]
        first_body = kw_args0.get('snippet')

        assert len(first_email_addresses) == 1, 'Just 1 org admin should be receiving the 1st email email'
        assert 'test@test.com' in first_email_addresses, 'Org admin email needs to be in recipient email list'
        assert 'email/content/contact_contributor_request.html' in first_body
        # assert 'You sent the following message' not in first_body, 'Fullname not "You" should appear in the 1st email'
        # assert 'REPLY ALL function' in first_body, 'Additional notes should be included in the 1st email'

        args1, kw_args1 = mocked_mail_recipient.call_args_list[1]
        second_email_addresses = [args1[0][0].get('email')]
        second_body = kw_args1.get('snippet')

        assert len(second_email_addresses) == 1, 'Just the requester should be receiving the 2nd email'
        assert data_dict.get('email') in second_email_addresses, 'Requester email needs to be in recipient email list'
        assert 'email/content/contact_contributor_request_confirmation_to_user.html' in second_body

        pkg_dict = self._get_action('package_show')({}, {"id": "test_dataset_1"})
        maintainer = pkg_dict.get("maintainer")
        assert maintainer
        m_user = model.User.get(maintainer)
        recipients_list = [args0[0][0]]
        assert {'display_name': m_user.display_name, 'email': m_user.email} in recipients_list
