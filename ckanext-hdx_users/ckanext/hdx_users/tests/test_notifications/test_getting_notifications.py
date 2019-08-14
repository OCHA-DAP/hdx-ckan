import ckan.tests.factories as factories
import ckan.plugins.toolkit as tk
import ckan.authz as authz
import ckan.model as model

import ckanext.hdx_theme.tests.hdx_test_with_inds_and_orgs as hdx_test_with_inds_and_orgs

from ckanext.hdx_org_group.helpers.static_lists import ORGANIZATION_TYPE_LIST
from ckanext.hdx_users.helpers.notification_service import MembershipRequestsService,\
    RequestDataService, SysadminRequestDataService
from ckanext.hdx_users.helpers.notifications_dao import MembershipRequestsDao, RequestDataDao

get_action = tk.get_action


class TestGettingNotifications(hdx_test_with_inds_and_orgs.HDXWithIndsAndOrgsTest):

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

    def test_get_org_membership_requests(self):
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
            "dataset_date": "01/01/1960-12/31/2012",
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

