import mock
import dateutil.parser as date_parser

import ckan.tests.factories as factories
import ckan.plugins.toolkit as tk
import ckan.authz as authz
import ckan.model as model

import ckanext.hdx_theme.tests.hdx_test_base as hdx_test_base
from ckanext.hdx_org_group.helpers.static_lists import ORGANIZATION_TYPE_LIST
from ckanext.hdx_users.helpers.notifications_dao import QuarantinedDatasetsDao
from ckanext.hdx_users.helpers.notification_service import QuarantinedDatasetsService, \
    SysadminQuarantinedDatasetsService

config = tk.config
NotAuthorized = tk.NotAuthorized
_get_action = tk.get_action


class TestQuarantineNotifications(hdx_test_base.HdxBaseTest):

    EDITOR_USER = 'editor_user'
    SYSADMIN_USER = 'testsysadmin'
    PACKAGE_ID = 'test_dataset_4_quarantine'
    RESOURCE_ID = None

    @classmethod
    def setup_class(cls):
        super(TestQuarantineNotifications, cls).setup_class()
        factories.User(name=cls.EDITOR_USER, email='quarantine_user@hdx.hdxtest.org')
        factories.Organization(
            name='org_name_4_quarantine',
            title='ORG NAME FOR QUARANTINE',
            users=[
                {'name': cls.EDITOR_USER, 'capacity': 'editor'},
            ],
            hdx_org_type=ORGANIZATION_TYPE_LIST[0][1],
            org_url='https://hdx.hdxtest.org/'
        )
        package = {
            "package_creator": "test function",
            "private": False,
            "dataset_date": "[1960-01-01 TO 2012-12-31]",
            "caveats": "These are the caveats",
            "license_other": "TEST OTHER LICENSE",
            "methodology": "This is a test methodology",
            "dataset_source": "Test data",
            "license_id": "hdx-other",
            "name": cls.PACKAGE_ID,
            "notes": "This is a test dataset",
            "title": "Test Dataset for Quarantine",
            "owner_org": "org_name_4_quarantine",
            "groups": [{"name": "roger"}],
            "resources": [
                {
                    'package_id': 'test_private_dataset_1',
                    'url': config.get('ckan.site_url', '') + '/storage/f/test_folder/hdx_test.csv',
                    'resource_type': 'file.upload',
                    'format': 'CSV',
                    'name': 'hdx_test.csv'
                }
            ]
        }
        context = {'model': model, 'session': model.Session, 'user': cls.EDITOR_USER}
        dataset_dict = _get_action('package_create')(context, package)
        cls.RESOURCE_ID = dataset_dict['resources'][0]['id']

    @staticmethod
    def __get_quarantine_service(username):
        userobj = model.User.get(username)
        is_sysadmin = authz.is_sysadmin(username)
        quarantined_datasets_dao = QuarantinedDatasetsDao(model, userobj, is_sysadmin)

        quarantine_service = SysadminQuarantinedDatasetsService (quarantined_datasets_dao, username) if is_sysadmin \
            else QuarantinedDatasetsService(quarantined_datasets_dao, username)

        return quarantine_service

    @staticmethod
    def __hdx_qa_resource_patch(package_id, resource_id, key, new_value, username):
        try:
            _get_action('hdx_qa_resource_patch')(
                {
                    'model': model, 'session': model.Session,
                    'user': username,
                },
                {'id': resource_id, key: new_value}
            )
        except NotAuthorized as e:
            pass
        return _get_action('package_show')({}, {'id': package_id})

    def test_quarantine(self):
        self.__hdx_qa_resource_patch(self.PACKAGE_ID, self.RESOURCE_ID, 'in_quarantine', True, self.SYSADMIN_USER)
        quarantine_service = self.__get_quarantine_service(self.EDITOR_USER)
        notifications_list = quarantine_service.get_quarantined_datasets_info()

        assert len(notifications_list) == 1
        assert notifications_list[0]['dataset'].get('name') == self.PACKAGE_ID
        assert not notifications_list[0]['for_sysadmin']

        quarantine_service = self.__get_quarantine_service(self.SYSADMIN_USER)
        notifications_list = quarantine_service.get_quarantined_datasets_info()

        assert len(notifications_list) == 1
        assert notifications_list[0]['dataset'].get('name') == self.PACKAGE_ID
        assert notifications_list[0]['for_sysadmin']
