import mock

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
        except toolkit.NotAuthorized, e:
            assert True, 'Calling hdx_send_mail_contributor without user should raise NotAuthorized'
        except Exception, e:
            assert False, 'Calling hdx_send_mail_contributor without user should raise NotAuthorized and not {}'.format(
                type(e).__name__)

        normal_user = factories.User()
        context = {
            'model': model,
            'session': model.Session,
            'user': normal_user['name']
        }

        self._get_action('hdx_send_mail_contributor')(context, data_dict)

        args, kw_args = mocked_mail_recipient.call_args

        recipient_emails = [recipient.get('email') for recipient in kw_args.get('recipients_list', [])]

        assert len(recipient_emails) == 2, 'Org admin and the requesting user should be receiving the email'
        assert 'test@test.com' in recipient_emails, 'Org admin email needs to be in recipient email list'
