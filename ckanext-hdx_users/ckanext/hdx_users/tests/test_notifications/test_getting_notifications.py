import mock
import dateutil.parser as date_parser

import ckan.tests.factories as factories
import ckan.plugins.toolkit as tk
import ckan.authz as authz
import ckan.model as model

import ckanext.hdx_theme.tests.hdx_test_base as hdx_test_base

from ckanext.hdx_org_group.helpers.static_lists import ORGANIZATION_TYPE_LIST
from ckanext.hdx_users.helpers.notification_service import MembershipRequestsService,\
    RequestDataService, SysadminRequestDataService
from ckanext.hdx_users.helpers.notifications_dao import MembershipRequestsDao, RequestDataDao

from ckanext.hdx_users.helpers.helpers import hdx_get_user_notifications

get_action = tk.get_action


class TestGettingNotifications(hdx_test_base.HdxBaseTest):

    ORG_NAME = 'notification_test_org'
    ORG_TITLE = 'Notification Test Org'
    ADMIN_USER = 'organization_administrator1'
    NORMAL_USER1 = 'normal_user1'
    NORMAL_USER2 = 'normal_user2'

    @classmethod
    def setup_class(cls):
        super(TestGettingNotifications, cls).setup_class()
        factories.User(name=cls.ADMIN_USER, email='organization_administrator1@hdx.hdxtest.org')
        factories.User(name=cls.NORMAL_USER1, email='normal_user1@hdx.hdxtest.org')
        factories.User(name=cls.NORMAL_USER2, email='normal_user2@hdx.hdxtest.org')
        factories.Organization(
            name=cls.ORG_NAME,
            title=cls.ORG_TITLE,
            users=[
                {'name': cls.ADMIN_USER, 'capacity': 'admin'},
            ],
            hdx_org_type=ORGANIZATION_TYPE_LIST[0][1],
            org_url='https://hdx.hdxtest.org/'
        )

    @mock.patch('ckanext.ytp.request.logic.hdx_mailer')
    def test_get_org_membership_requests(self, hdx_mail_mock):
        req1 = self._request_membership(self.NORMAL_USER1)
        req2 = self._request_membership(self.NORMAL_USER2)
        request_list = self.get_membership_request_service(self.ADMIN_USER).get_org_membership_requests()
        # request_list = notifications.get_org_membership_requests(
        #     context={'ignore_auth': True, 'user': 'organization_administrator1'})

        assert len(request_list) == 1
        assert request_list[0].get('org_title') == self.ORG_TITLE
        assert request_list[0].get('org_name') == self.ORG_NAME
        assert request_list[0].get('count') == 2

        self._approve_membership(req1['id'])

        request_list = self.get_membership_request_service(self.ADMIN_USER).get_org_membership_requests()

        # request_list = notifications.get_org_membership_requests(
        #     context={'ignore_auth': True, 'user': 'organization_administrator1'})
        assert len(request_list) == 1
        assert request_list[0].get('count') == 1

        # cleaning up notifications
        self._approve_membership(req2['id'])

    def test_get_requestdata_request(self):
        pkg_dict = self._create_request_data_dataset()
        self._create_request_data_request(pkg_dict['id'])

        request_data_service = self.get_request_data_service(self.ADMIN_USER)
        request_list = request_data_service.get_requestdata_requests()

        assert len(request_list) == 1
        assert not request_list[0].get('for_sysadmin')
        assert not request_list[0].get('is_sysadmin')
        assert request_list[0].get('count') == 1

        request_data_service_for_sysadmin = self.get_request_data_service('testsysadmin')
        request_list_for_sysadmin = request_data_service_for_sysadmin.get_requestdata_requests()

        assert len(request_list_for_sysadmin) == 1
        assert request_list_for_sysadmin[0].get('for_sysadmin')
        assert request_list_for_sysadmin[0].get('is_sysadmin')
        assert request_list_for_sysadmin[0].get('count') == 1

        self._delete_request_data_request(pkg_dict['id'])

    @mock.patch('ckanext.hdx_users.helpers.notification_service.MembershipRequestsService')
    @mock.patch('ckanext.hdx_users.helpers.notification_service.RequestDataService')
    @mock.patch('ckanext.hdx_users.helpers.notification_service.g')
    @mock.patch('ckanext.hdx_users.helpers.helpers.g')
    def test_get_user_notifications_helper(self, mock_helpers_g, mock_notifications_g,
                                           MockRequestDataService, MockMembershipRequestService):
        dates = [
            {'datestr': '2019-08-01T08:35:01'},
            {'datestr': '2019-08-04T08:35:01'},
            {'datestr': '2019-08-03T08:35:01'},
            {'datestr': '2019-08-02T08:35:01'},
        ]
        for date in dates:
            date['date'] = date_parser.parse(date['datestr'])
            date['formatted_date'] = date['date'].strftime('%b %-d, %Y')

        sorted_dates = sorted(dates, key=lambda d: d['date'], reverse=True)

        mock_notifications_g.user = self.ADMIN_USER
        mock_helpers_g.hdx_user_notifications = None

        MockMembershipRequestService.return_value.get_org_membership_requests.return_value = [
            {
                'org_title': 'Org 1',
                'org_name': 'org1',
                'org_hdx_url': '',
                'html_template': 'light/notifications/org_membership_snippet.html',
                'last_date': dates[0]['date'],
                'count': 1,
                'for_sysadmin': False,
                'is_sysadmin': False
            },
            {
                'org_title': 'Org 2',
                'org_name': 'org2',
                'org_hdx_url': '',
                'html_template': 'light/notifications/org_membership_snippet.html',
                'last_date': dates[1]['date'],
                'count': 1,
                'for_sysadmin': False,
                'is_sysadmin': False
            }
        ]

        MockRequestDataService.return_value.get_requestdata_requests.return_value = [
            {
                'last_date': dates[2]['date'],
                'count': 1,
                'html_template': 'light/notifications/requestdata_snippet.html',
                'my_requests_url': '',
                'for_sysadmin': False,
                'is_sysadmin': False
            },
            {
                'last_date': dates[3]['date'],
                'count': 1,
                'html_template': 'light/notifications/requestdata_snippet.html',
                'my_requests_url': '',
                'for_sysadmin': False,
                'is_sysadmin': False
            }
        ]
        result = hdx_get_user_notifications()

        assert result['count'] == 4
        assert result['list'][0]['last_date'] == sorted_dates[0]['formatted_date']
        assert 'org_hdx_url' in result['list'][0], 'The notification should be of type membership request'

        assert result['list'][1]['last_date'] == sorted_dates[1]['formatted_date']
        assert 'my_requests_url' in result['list'][1], 'The notification should be of type requestdata'

        assert result['list'][2]['last_date'] == sorted_dates[2]['formatted_date']
        assert 'my_requests_url' in result['list'][2], 'The notification should be of type requestdata'

        assert result['list'][3]['last_date'] == sorted_dates[3]['formatted_date']
        assert 'org_hdx_url' in result['list'][3], 'The notification should be of type membership request'


    @staticmethod
    def get_membership_request_service(username):
        userobj = model.User.get(username)
        is_sysadmin = authz.is_sysadmin(username)
        membership_request_dao = MembershipRequestsDao(model, userobj, is_sysadmin)

        membership_request_service = MembershipRequestsService(membership_request_dao, is_sysadmin)

        return membership_request_service

    @staticmethod
    def get_request_data_service(username):
        userobj = model.User.get(username)
        is_sysadmin = authz.is_sysadmin(username)
        request_data_dao = RequestDataDao(model, userobj, is_sysadmin)

        request_data_service = SysadminRequestDataService(request_data_dao, username)\
            if is_sysadmin else RequestDataService(request_data_dao, username)

        return request_data_service

    @classmethod
    def _request_membership(cls, username):
        return get_action('member_request_create')(
            {'user': username, 'ignore_auth': True},
            {'role': 'member', 'group': cls.ORG_NAME}
        )

    @classmethod
    def _approve_membership(cls, member_id):
        get_action('member_request_process')(
            {'user': cls.ADMIN_USER, 'ignore_auth': True},
            {'member': member_id, 'approve': True}
        )

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
            "name": "requestdata_package_for_notifications",
            "notes": "This is a test activity",
            "title": "Requestdata package for notifications",
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

    @classmethod
    def _create_request_data_request(cls, package_id):
        data_dict = {
            'package_id': package_id,
            'sender_name': 'Normal User1',
            'message_content': 'I want to add additional data.',
            'organization': cls.ORG_TITLE,
            'email_address': 'test@test.com',
        }

        return get_action('requestdata_request_create')({'user': cls.NORMAL_USER1}, data_dict)

    @classmethod
    def _delete_request_data_request(cls, package_id):
        get_action('requestdata_request_delete_by_package_id')({'user': cls.ADMIN_USER}, {'package_id': package_id})

