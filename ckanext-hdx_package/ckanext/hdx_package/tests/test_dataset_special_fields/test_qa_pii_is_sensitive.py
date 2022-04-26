import pytest
import os
import six

from werkzeug.datastructures import FileStorage

import ckan.logic as logic
import ckan.model as model
import ckan.plugins.toolkit as tk
import ckan.tests.factories as factories
import ckanext.hdx_theme.tests.hdx_test_base as hdx_test_base
from ckanext.hdx_org_group.helpers.static_lists import ORGANIZATION_TYPE_LIST

config = tk.config
NotAuthorized = tk.NotAuthorized
NotFound = logic.NotFound


class TestQAPIIIsSensitiveNormalUser(hdx_test_base.HdxBaseTest):
    NORMAL_USER = 'quarantine_user'
    SYSADMIN_USER = 'testsysadmin'
    PACKAGE_ID = 'test_dataset_2'

    # PACKAGE_ID = 'test_dataset_1_microdata'

    @classmethod
    def _get_action(cls, action_name):
        return tk.get_action(action_name)

    @classmethod
    def setup_class(cls):
        super(TestQAPIIIsSensitiveNormalUser, cls).setup_class()
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
            "dataset_date": "01/01/1960-12/31/2012",
            "caveats": "These are the caveats",
            "license_other": "TEST OTHER LICENSE",
            "methodology": "This is a test methodology",
            "dataset_source": "Test data",
            "license_id": "hdx-other",
            "name": cls.PACKAGE_ID,
            "notes": "This is a test dataset",
            "title": "Test Dataset for Quarantine 2",
            "owner_org": "org_name_4_quarantine",
            "groups": [{"name": "roger"}],
            "resources": [
                {
                    'package_id': 'test_dataset_2',
                    'url': config.get('ckan.site_url', '') + '/storage/f/test_folder/hdx_test.csv',
                    'resource_type': 'file.upload',
                    'format': 'CSV',
                    'name': 'hdx_test1.csv',
                },
                {
                    'package_id': 'test_dataset_2',
                    'url': config.get('ckan.site_url', '') + '/storage/f/test_folder/hdx_test.csv',
                    'resource_type': 'file.upload',
                    'format': 'CSV',
                    'name': 'hdx_test2.csv',
                },
                {
                    'package_id': 'test_dataset_2',
                    'url': config.get('ckan.site_url', '') + '/storage/f/test_folder/hdx_test.csv',
                    'resource_type': 'file.upload',
                    'format': 'CSV',
                    'name': 'hdx_test3.csv',
                },
                {
                    'package_id': 'test_dataset_2',
                    'url': config.get('ckan.site_url', '') + '/storage/f/test_folder/hdx_test.csv',
                    'resource_type': 'file.upload',
                    'format': 'CSV',
                    'name': 'hdx_test4.csv',
                }

            ]
        }

        context = {'model': model, 'session': model.Session, 'user': cls.NORMAL_USER}
        dataset_dict = cls._get_action('package_create')(context, package)

    def test_normal_user_check_pii_is_sensitive(self):
        context = {'model': model, 'session': model.Session, 'user': self.NORMAL_USER}
        package_dict = self._get_action('package_show')(context, {'id': self.PACKAGE_ID})
        assert 'pii_is_sensitive' not in package_dict.get('resources')[0]
        assert 'pii_is_sensitive' not in package_dict.get('resources')[1]
        assert 'pii_is_sensitive' not in package_dict.get('resources')[2]
        assert 'pii_is_sensitive' not in package_dict.get('resources')[3]


class TestQAPIIIsSensitiveQAOfficer(hdx_test_base.HdxBaseTest):
    NORMAL_USER = 'quarantine_user'
    SYSADMIN_USER = 'testsysadmin'
    PACKAGE_ID = 'test_dataset_2'

    # PACKAGE_ID = 'test_dataset_1_microdata'

    @classmethod
    def _get_action(cls, action_name):
        return tk.get_action(action_name)

    @classmethod
    def setup_class(cls):
        super(TestQAPIIIsSensitiveQAOfficer, cls).setup_class()
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
            "dataset_date": "01/01/1960-12/31/2012",
            "caveats": "These are the caveats",
            "license_other": "TEST OTHER LICENSE",
            "methodology": "This is a test methodology",
            "dataset_source": "Test data",
            "license_id": "hdx-other",
            "name": cls.PACKAGE_ID,
            "notes": "This is a test dataset",
            "title": "Test Dataset for Quarantine 2",
            "owner_org": "org_name_4_quarantine",
            "groups": [{"name": "roger"}],
            "resources": [
                {
                    'package_id': 'test_dataset_2',
                    'url': config.get('ckan.site_url', '') + '/storage/f/test_folder/hdx_test.csv',
                    'resource_type': 'file.upload',
                    'format': 'CSV',
                    'name': 'hdx_test1.csv',
                },
                {
                    'package_id': 'test_dataset_2',
                    'url': config.get('ckan.site_url', '') + '/storage/f/test_folder/hdx_test.csv',
                    'resource_type': 'file.upload',
                    'format': 'CSV',
                    'name': 'hdx_test2.csv',
                },
                {
                    'package_id': 'test_dataset_2',
                    'url': config.get('ckan.site_url', '') + '/storage/f/test_folder/hdx_test.csv',
                    'resource_type': 'file.upload',
                    'format': 'CSV',
                    'name': 'hdx_test3.csv',
                },
                {
                    'package_id': 'test_dataset_2',
                    'url': config.get('ckan.site_url', '') + '/storage/f/test_folder/hdx_test.csv',
                    'resource_type': 'file.upload',
                    'format': 'CSV',
                    'name': 'hdx_test4.csv',
                }

            ]
        }
        context = {'model': model, 'session': model.Session, 'user': cls.NORMAL_USER}
        dataset_dict = cls._get_action('package_create')(context, package)

    def test_qa_officer_change_pii_is_sensitive(self):
        context = {'model': model, 'session': model.Session, 'user': self.SYSADMIN_USER}
        package_dict = self._get_action('package_show')(context, {'id': self.PACKAGE_ID})
        assert 'pii_is_sensitive' not in package_dict.get('resources')[0]
        assert 'pii_is_sensitive' not in package_dict.get('resources')[1]
        assert 'pii_is_sensitive' not in package_dict.get('resources')[2]
        assert 'pii_is_sensitive' not in package_dict.get('resources')[3]

        try:
            result = self._get_action('hdx_qa_package_revise_resource')(context, {'id': self.PACKAGE_ID})
            assert False
        except NotFound as ex:
            assert 'package id, key or value were not provided' in ex.message

        try:
            result = self._get_action('hdx_qa_package_revise_resource')(context, {'id': self.PACKAGE_ID,
                                                                                'key': 'pii_is_sensitive'})
            assert False
        except NotFound as ex:
            assert 'package id, key or value were not provided' in ex.message

        self._get_action('hdx_qa_package_revise_resource')(context, {'id': package_dict.get('id'),
                                                                     'key': 'pii_is_sensitive',
                                                                     'value': 'True'})
        package_dict = self._get_action('package_show')(context, {'id': self.PACKAGE_ID})

        assert 'pii_is_sensitive' in package_dict.get('resources')[0]
        assert 'pii_is_sensitive' in package_dict.get('resources')[1]
        assert 'pii_is_sensitive' in package_dict.get('resources')[2]
        assert 'pii_is_sensitive' in package_dict.get('resources')[3]
        assert package_dict.get('resources')[0]['pii_is_sensitive']
        assert package_dict.get('resources')[1]['pii_is_sensitive']
        assert package_dict.get('resources')[2]['pii_is_sensitive']
        assert package_dict.get('resources')[3]['pii_is_sensitive']


class TestQAPIIIsSensitiveReset(hdx_test_base.HdxBaseTest):

    SYSADMIN_USER = 'testsysadmin'

    FILE1_NAME = 'data1.csv'
    FILE2_NAME = 'data2.csv'

    CONTEXT = {'model': model, 'session': model.Session, 'user': SYSADMIN_USER}

    @classmethod
    def setup_class(cls):
        super(TestQAPIIIsSensitiveReset, cls).setup_class()
        factories.Organization(
            name='org_name_4_pii_is_sensitive_reset_check',
            title='ORG NAME FOR PII IS SENSITIVE RESET CHECK',
            hdx_org_type=ORGANIZATION_TYPE_LIST[0][1],
            org_url='https://hdx.hdxtest.org/'
        )

    @classmethod
    def _get_action(cls, action_name):
        return tk.get_action(action_name)

    @classmethod
    def create_packages_by_user(cls, pkg_id):
        package = {
            "package_creator": "test function",
            "private": False,
            "dataset_date": "[1960-01-01 TO 2012-12-31]",
            "caveats": "These are the caveats",
            "license_other": "TEST OTHER LICENSE",
            "methodology": "This is a test methodology",
            "dataset_source": "Test data",
            "license_id": "hdx-other",
            "name": pkg_id,
            "notes": "This is a test dataset",
            "title": "Test Dataset for QA Completed " + pkg_id,
            "owner_org": "org_name_4_pii_is_sensitive_reset_check",
            "groups": [{"name": "roger"}],
            "resources": [
                {
                    'package_id': pkg_id,
                    'url': config.get('ckan.site_url', '') + '/storage/f/test_folder/hdx_test.csv',
                    'resource_type': 'file.upload',
                    'format': 'CSV',
                    'name': 'hdx_test1.csv'
                },
                {
                    'package_id': pkg_id,
                    'url': config.get('ckan.site_url', '') + '/storage/f/test_folder/hdx_test.csv',
                    'resource_type': 'file.upload',
                    'format': 'CSV',
                    'name': 'hdx_test2.csv'
                },
            ]
        }
        context = {'model': model, 'session': model.Session, 'user': cls.SYSADMIN_USER}
        return cls._get_action('package_create')(context, package)

    def test_pii_is_sensitive_reset_on_package_revise(self):
        dataset_dict = self.create_packages_by_user('dataset-4-pii_is_sensitive-reset-on-package_revise')

        self._get_action('hdx_qa_package_revise_resource')(self.CONTEXT, {'id': dataset_dict['id'],
                                                                     'key': 'pii_is_sensitive',
                                                                     'value': 'True'})
        modified1_dataset_dict = self._get_action('package_show')(self.CONTEXT, {'id': dataset_dict['id']})
        assert modified1_dataset_dict['resources'][0]['pii_is_sensitive']
        assert modified1_dataset_dict['resources'][1]['pii_is_sensitive']

        file_path1 = os.path.join(os.path.dirname(__file__), self.FILE1_NAME)
        file_path2 = os.path.join(os.path.dirname(__file__), self.FILE2_NAME)
        with open(file_path1, 'rb') as f1, open(file_path2, 'rb') as f2:
            file_upload1 = FileStorage(f1)
            file_upload2 = FileStorage(f2)
            revise_dict = self._get_action('package_revise')(self.CONTEXT,
                                                         {
                                                             'match__id': dataset_dict['id'],
                                                             'update__resources__0__upload': file_upload1,
                                                             'update__resources__1__upload': file_upload2,

                                                         })

            modified2_dataset_dict = revise_dict['package']
            assert 'pii_is_sensitive' not in modified2_dataset_dict['resources'][0]
            assert 'pii_is_sensitive' not in modified2_dataset_dict['resources'][1]

    def test_pii_is_sensitive_reset_on_resource_update(self):
        dataset_dict = self.create_packages_by_user('dataset-4-pii_is_sensitive-reset-on-resource_update')

        self._get_action('hdx_qa_package_revise_resource')(self.CONTEXT, {'id': dataset_dict['id'],
                                                                     'key': 'pii_is_sensitive',
                                                                     'value': 'True'})
        modified1_dataset_dict = self._get_action('package_show')(self.CONTEXT, {'id': dataset_dict['id']})
        resource0 = modified1_dataset_dict['resources'][0]
        resource1 = modified1_dataset_dict['resources'][1]
        assert resource0['pii_is_sensitive']
        assert resource1['pii_is_sensitive']

        file_path1 = os.path.join(os.path.dirname(__file__), self.FILE1_NAME)
        file_path2 = os.path.join(os.path.dirname(__file__), self.FILE2_NAME)
        with open(file_path1, 'rb') as f1, open(file_path2, 'rb') as f2:
            file_upload0 = FileStorage(f1)
            file_upload1 = FileStorage(f2)
            modified_resource0 = self._get_action('resource_update')(self.CONTEXT,
                                                                     {
                                                                         'id': resource0['id'],
                                                                         'url': 'data1.csv',
                                                                         'resource_type': 'file.upload',
                                                                         'format': 'CSV',
                                                                         'name': 'data1.csv',
                                                                         'upload': file_upload0

                                                                     })
            modified_resource1 = self._get_action('resource_update')(self.CONTEXT,
                                                                     {
                                                                         'id': resource1['id'],
                                                                         'url': 'data2.csv',
                                                                         'resource_type': 'file.upload',
                                                                         'format': 'CSV',
                                                                         'name': 'data2.csv',
                                                                         'upload': file_upload1

                                                                     })

            assert 'pii_is_sensitive' not in modified_resource0
            assert 'pii_is_sensitive' not in modified_resource1
