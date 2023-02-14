import mock

import ckan.model as model
import ckan.plugins.toolkit as tk
import ckan.tests.factories as factories
from ckanext.hdx_org_group.helpers.static_lists import ORGANIZATION_TYPE_LIST
from ckan.lib.helpers import url_for

import ckanext.hdx_theme.tests.hdx_test_with_inds_and_orgs as hdx_test_with_inds_and_orgs

get_action = tk.get_action


class TestRequestDataEmails(hdx_test_with_inds_and_orgs.HDXWithIndsAndOrgsTest):
    ORG_NAME = 'email_test_org'
    ORG_TITLE = 'Email Test Organization'
    ADMIN_USER = 'organization_administrator1'

    @classmethod
    def setup_class(cls):
        super(TestRequestDataEmails, cls).setup_class()
        factories.User(name=cls.ADMIN_USER, email='organization_administrator1@hdx.hdxtest.org')
        factories.Organization(
            name=cls.ORG_NAME,
            title=cls.ORG_TITLE,
            users=[
                {'name': cls.ADMIN_USER, 'capacity': 'admin'},
            ],
            hdx_org_type=ORGANIZATION_TYPE_LIST[0][1],
            org_url='https://hdx.hdxtest.org/'
        )

    @mock.patch('ckanext.hdx_package.actions.get.hdx_mailer.mail_recipient')
    def test_send_request(self, mocked_mail_recipient):
        member = model.User.by_name('tester')
        member.email = 'tester@test.com'

        sysadmin = model.User.by_name('testsysadmin')
        sysadmin.email = 'testsysadmin@test.com'

        auth = {'Authorization': str(sysadmin.apikey)}

        pkg_dict = self._create_request_data_dataset()

        post_params = {
            'package_id': pkg_dict['id'],
            'sender_name': 'Normal User1',
            'message_content': 'I want to add additional data.',
            'organization': self.ORG_TITLE,
            'email_address': 'test@test.com',
            'sender_country': 'Romania',
            'sender_organization_id': 'hdx-test-org',
            'sender_organization_type': 'Military',
            'sender_intend': 'Research Purposes'
        }

        url = url_for('requestdata_send_request.send_request')

        res = self.app.post(url, params=post_params, extra_environ=auth)

        assert '{"success": true, "message": "Email message was successfully sent."}' in res.body

        args, kw_args = mocked_mail_recipient.call_args

        assert len(args[0]) == 1, 'mail goes to sender'
        assert post_params['message_content'] in args[2].get('msg')
        assert 'email/content/request_data_to_user.html' == kw_args.get('snippet')

    @classmethod
    def _create_request_data_dataset(cls):
        package = {
            "package_creator": "testsysadmin",
            "private": False,
            "dataset_date": "[1960-01-01 TO 2012-12-31]",
            "indicator": "0",
            "caveats": "These are the caveats",
            "license_other": "TEST OTHER LICENSE",
            "methodology": "This is a test methodology",
            "dataset_source": "World Bank",
            "license_id": "hdx-other",
            "name": "requestdata_package_for_emails",
            "notes": "This is a test activity",
            "title": "Requestdata package for emails",
            "groups": [{"name": "roger"}],
            "owner_org": cls.ORG_NAME,
            "maintainer": cls.ADMIN_USER,
            "is_requestdata_type": True,
            "file_types": ["csv"],
            "field_names": ["field1", "field2"]
        }

        context = {'ignore_auth': True,
                   'model': model, 'session': model.Session, 'user': 'testsysadmin'}

        return get_action('package_create')(context, package)
