import pytest
import mock

import ckan.tests.factories as factories
import ckan.model as model
import ckan.plugins.toolkit as tk

import ckanext.hdx_theme.tests.hdx_test_base as hdx_test_base

from ckanext.hdx_package.actions.patch import _send_analytics_for_pii_if_needed, _send_analytics_for_sdc_if_needed
from ckanext.hdx_org_group.helpers.static_lists import ORGANIZATION_TYPE_LIST

config = tk.config
NotAuthorized = tk.NotAuthorized

analytics_sender = None


def _send_analytics_for_pii_if_needed_mocked(*args, **kwargs):
    global analytics_sender
    analytics_sender = _send_analytics_for_pii_if_needed(*args, **kwargs)


def _send_analytics_for_sdc_if_needed_mocked(*args, **kwargs):
    global analytics_sender
    analytics_sender = _send_analytics_for_sdc_if_needed(*args, **kwargs)


class TestPiiSdcMetafields(hdx_test_base.HdxBaseTest):

    NORMAL_USER = 'quarantine_user'
    SYSADMIN_USER = 'testsysadmin'
    PACKAGE_ID = 'test_dataset_4_quarantine'
    RESOURCE_ID = None
    DATASET_ID = None

    @classmethod
    def _get_action(cls, action_name):
        return tk.get_action(action_name)

    @classmethod
    def setup_class(cls):
        super(TestPiiSdcMetafields, cls).setup_class()
        factories.User(name=cls.NORMAL_USER, email='quarantine_user@hdx.hdxtest.org')
        factories.Organization(
            name='org_name_4_quarantine',
            title='ORG NAME FOR QUARANTINE',
            users=[
                {'name': cls.NORMAL_USER, 'capacity': 'admin'},
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
                    'url': config.get('ckan.site_url', '') + '/storage/f/test_folder/hdx_test.csv',
                    'resource_type': 'file.upload',
                    'format': 'CSV',
                    'name': 'hdx_test.csv'
                }
            ]
        }

        context = {'model': model, 'session': model.Session, 'user': cls.NORMAL_USER}
        dataset_dict = cls._get_action('package_create')(context, package)
        cls.RESOURCE_ID = dataset_dict['resources'][0]['id']
        cls.DATASET_ID = dataset_dict['id']

    @mock.patch('ckanext.hdx_package.actions.patch.tag_s3_version_by_resource_id')
    def test_normal_user_cannot_modify_quarantine(self, tag_s3_mock):
        package_dict = self._change_resource_field_via_resource_patch(self.RESOURCE_ID, 'in_quarantine', True,
                                                                      self.SYSADMIN_USER)
        assert 'in_quarantine' not in package_dict['resources'][0]

        package_dict = self._hdx_qa_resource_patch(self.RESOURCE_ID, 'in_quarantine', True,
                                                                      self.SYSADMIN_USER)
        assert package_dict['resources'][0]['in_quarantine'] is True

        package_dict = self._change_resource_field_via_resource_patch(self.RESOURCE_ID, 'in_quarantine', False,
                                                                      self.NORMAL_USER)
        assert package_dict['resources'][0]['in_quarantine'] is True

        package_dict = self._hdx_qa_resource_patch(self.RESOURCE_ID, 'in_quarantine', False,
                                                                      self.NORMAL_USER)
        assert package_dict['resources'][0]['in_quarantine'] is True

        package_dict = self._change_resource_field_via_resource_patch(self.RESOURCE_ID, 'in_quarantine', False,
                                                                      self.SYSADMIN_USER)
        assert package_dict['resources'][0]['in_quarantine'] is True

        package_dict = self._hdx_qa_resource_patch(self.RESOURCE_ID, 'in_quarantine', False,
                                                                      self.SYSADMIN_USER)
        assert package_dict['resources'][0]['in_quarantine'] is False

    def test_multiple_pii_fields_can_be_set(self):
        context = {'model': model, 'session': model.Session, 'user': self.SYSADMIN_USER}
        resource2 = {
            'package_id': self.PACKAGE_ID,
            'url': config.get('ckan.site_url', '') + '/storage/f/test_folder/hdx_test.csv',
            'resource_type': 'file.upload',
            'format': 'CSV',
            'name': 'hdx_test2.csv'
        }
        res2_dict = self._get_action('resource_create')(context, resource2)

        changes_dict = {
            'id': res2_dict['id'],
            'pii_report_flag': 'OK',
            'pii_timestamp': '2023-02-08T23:21:01.345000',
            'pii_report_id': '/some_path/some.log'
        }
        modified_res2_dict = self._get_action('hdx_qa_resource_patch')(context, changes_dict)

        for key, value in changes_dict.items():
            assert modified_res2_dict.get(key) == value

        self._get_action('resource_delete')(context, {'id': res2_dict['id']})

    @mock.patch('ckanext.hdx_package.helpers.analytics.g')
    @mock.patch('ckanext.hdx_package.actions.patch._send_analytics_for_pii_if_needed',
                wraps=_send_analytics_for_pii_if_needed_mocked)
    @mock.patch('ckanext.hdx_theme.util.analytics.AbstractAnalyticsSender.send_to_queue')
    def test_pii_tracking(self, send_to_queue_mock, send_analytics_mock, g_mock):
        global analytics_sender
        g_mock.user = self.SYSADMIN_USER
        context = {'model': model, 'session': model.Session, 'user': self.SYSADMIN_USER}
        resource2 = {
            'package_id': self.PACKAGE_ID,
            'url': config.get('ckan.site_url', '') + '/storage/f/test_folder/hdx_test.csv',
            'resource_type': 'file.upload',
            'format': 'CSV',
            'name': 'hdx_test2.csv'
        }
        res2_dict = self._get_action('resource_create')(context, resource2)

        changes_dict = {
            'id': res2_dict['id'],
            'pii_report_flag': 'OK',
            'pii_timestamp': '2023-02-08T23:21:01.345000',
            'pii_report_id': '/some_path/some.log'
        }
        self._get_action('hdx_qa_resource_patch')(context, changes_dict)
        call_count = send_to_queue_mock.call_count
        analytics_dict = analytics_sender.analytics_dict
        assert analytics_dict['event_name'] == 'qa set pii'
        assert analytics_dict['mixpanel_meta']['dataset name'] == 'test_dataset_4_quarantine'
        assert analytics_dict['mixpanel_meta']['org name'] == 'org_name_4_quarantine'
        assert analytics_dict['mixpanel_meta']['group names'][0] == 'roger'

        self._get_action('hdx_qa_resource_patch')(context, changes_dict)
        assert call_count == send_to_queue_mock.call_count, 'send_to_queue() shouldn\'t have been called ' \
                                                            'again because the pii_report_flag was the same'

        self._get_action('resource_delete')(context, {'id': res2_dict['id']})

    @mock.patch('ckanext.hdx_package.helpers.analytics.g')
    @mock.patch('ckanext.hdx_package.actions.patch._send_analytics_for_sdc_if_needed',
                wraps=_send_analytics_for_sdc_if_needed_mocked)
    @mock.patch('ckanext.hdx_theme.util.analytics.AbstractAnalyticsSender.send_to_queue')
    def test_sdc_tracking(self, send_to_queue_mock, send_analytics_mock, g_mock):
        global analytics_sender
        g_mock.user = self.SYSADMIN_USER
        context = {'model': model, 'session': model.Session, 'user': self.SYSADMIN_USER}
        resource2 = {
            'package_id': self.PACKAGE_ID,
            'url': config.get('ckan.site_url', '') + '/storage/f/test_folder/hdx_test.csv',
            'resource_type': 'file.upload',
            'format': 'CSV',
            'name': 'hdx_test2.csv'
        }
        res2_dict = self._get_action('resource_create')(context, resource2)

        changes_dict = {
            'id': res2_dict['id'],
            'sdc_report_flag': 'OK',
            'sdc_timestamp': '2023-02-08T23:21:01.345000',
            'sdc_report_id': '/some_path/some.log'
        }
        self._get_action('hdx_qa_resource_patch')(context, changes_dict)
        call_count = send_to_queue_mock.call_count
        analytics_dict = analytics_sender.analytics_dict
        assert analytics_dict['event_name'] == 'qa set sdc'
        assert analytics_dict['mixpanel_meta']['dataset name'] == 'test_dataset_4_quarantine'
        assert analytics_dict['mixpanel_meta']['org name'] == 'org_name_4_quarantine'
        assert analytics_dict['mixpanel_meta']['group names'][0] == 'roger'

        self._get_action('hdx_qa_resource_patch')(context, changes_dict)
        assert call_count == send_to_queue_mock.call_count, 'send_to_queue() shouldn\'t have been called ' \
                                                            'again because the sdc_report_flag was the same'

        self._get_action('resource_delete')(context, {'id': res2_dict['id']})

    def test_normal_user_cannot_modify_pii_timestamp(self):
        date_str = '2019-09-01T17:30:50.883601'

        package_dict = self._change_resource_field_via_resource_patch(self.RESOURCE_ID, 'pii_timestamp', date_str,
                                                                      self.SYSADMIN_USER)
        assert 'pii_timestamp' not in package_dict['resources'][0]

        package_dict = self._hdx_qa_resource_patch(self.RESOURCE_ID, 'pii_timestamp', date_str,
                                                                      self.SYSADMIN_USER)
        assert package_dict['resources'][0]['pii_timestamp'] == date_str

        package_dict = self._change_resource_field_via_resource_patch(self.RESOURCE_ID, 'pii_timestamp', '',
                                                                      self.NORMAL_USER)
        assert package_dict['resources'][0]['pii_timestamp'] == date_str

        package_dict = self._hdx_qa_resource_patch(self.RESOURCE_ID, 'pii_timestamp', '',
                                                                      self.NORMAL_USER)
        assert package_dict['resources'][0]['pii_timestamp'] == date_str

        package_dict = self._change_resource_field_via_resource_patch(self.RESOURCE_ID, 'pii_timestamp', '',
                                                                      self.SYSADMIN_USER)
        assert package_dict['resources'][0]['pii_timestamp'] == date_str

        package_dict = self._hdx_qa_resource_patch(self.RESOURCE_ID, 'pii_timestamp', '',
                                                                      self.SYSADMIN_USER)
        assert 'pii_timestamp' not in package_dict['resources'][0]

    def _change_resource_field_via_resource_patch(self, resource_id, key, new_value, username):
        self._get_action('resource_patch')(
            {
                'model': model, 'session': model.Session,
                'user': username,
            },
            {'id': resource_id, key: new_value}
        )
        return self._get_action('package_show')({}, {'id': self.PACKAGE_ID})

    def _hdx_qa_resource_patch(self, resource_id, key, new_value, username):
        try:
            self._get_action('hdx_qa_resource_patch')(
                {
                    'model': model, 'session': model.Session,
                    'user': username,
                },
                {'id': resource_id, key: new_value}
            )
        except NotAuthorized as e:
            pass
        return self._get_action('package_show')({}, {'id': self.PACKAGE_ID})

