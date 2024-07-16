import pytest

import ckan.tests.factories as factories
import ckan.model as model
import ckan.plugins.toolkit as tk

import ckanext.hdx_theme.tests.hdx_test_base as hdx_test_base

from ckanext.hdx_org_group.helpers.static_lists import ORGANIZATION_TYPE_LIST

config = tk.config
NotAuthorized = tk.NotAuthorized
ValidationError = tk.ValidationError


class TestDataUpdateFrequency(hdx_test_base.HdxBaseTest):
    NORMAL_USER = 'normal_user'
    LIVE_UPDATE_FREQUENCY = '0'

    INTERNAL_RESOURCE = {
        'package_id': 'test_private_dataset_1',
        'url': config.get('ckan.site_url', '') + '/storage/f/test_folder/hdx_test.csv',
        'resource_type': 'file.upload',
        'format': 'CSV',
        'name': 'hdx_test.csv'
    }
    EXTERNAL_RESOURCE = {
        'package_id': 'test_private_dataset_1',
        'url': 'http://test.ckan.test/test.csv',
        'resource_type': 'api',
        'url_type': 'api',
        'format': 'CSV',
        'name': 'data1.csv',
    }
    PACKAGE = {
        'package_creator': 'test function',
        'private': False,
        'dataset_date': '01/01/1960-12/31/2012',
        'caveats': 'These are the caveats',
        'license_other': 'TEST OTHER LICENSE',
        'methodology': 'This is a test methodology',
        'dataset_source': 'Test data',
        'license_id': 'hdx-other',
        'notes': 'This is a test dataset',
        'data_update_frequency': LIVE_UPDATE_FREQUENCY,
        'title': 'Test Dataset for Update Frequency',
        'owner_org': 'org_name_4_update_frequency',
        'groups': [{'name': 'roger'}],
    }

    @classmethod
    def _get_action(cls, action_name):
        return tk.get_action(action_name)

    @classmethod
    def setup_class(cls):
        super(TestDataUpdateFrequency, cls).setup_class()
        factories.User(name=cls.NORMAL_USER, email='normal_user@hdx.hdxtest.org')
        factories.Organization(
            name='org_name_4_update_frequency',
            title='ORG NAME FOR UPDATE FREQUENCY',
            users=[
                {'name': cls.NORMAL_USER, 'capacity': 'admin'},
            ],
            hdx_org_type=ORGANIZATION_TYPE_LIST[0][1],
            org_url='https://hdx.hdxtest.org/'
        )

    def test_valid_live_dataset_with_external_resource(self):
        context = {'model': model, 'session': model.Session, 'user': self.NORMAL_USER}

        self.PACKAGE['name'] = 'test_dataset_1'
        self.PACKAGE['resources'] = [self.INTERNAL_RESOURCE, self.EXTERNAL_RESOURCE]

        dataset_dict = self._get_action('package_create')(context, self.PACKAGE)
        assert dataset_dict.get(
            'data_update_frequency') == self.LIVE_UPDATE_FREQUENCY, 'Live dataset should be created successfully with ' \
                                                                    'an external resource'

    def test_invalid_live_dataset_with_only_internal_resources(self):
        context = {'model': model, 'session': model.Session, 'user': self.NORMAL_USER}

        self.PACKAGE['name'] = 'test_dataset_2'
        self.PACKAGE['resources'] = [self.INTERNAL_RESOURCE]

        try:
            self._get_action('package_create')(context, self.PACKAGE)
            assert False, 'Validation error should be raised for live datasets without any external resource'
        except ValidationError as e:
            assert True, 'Live datasets should have at least one external resource'
