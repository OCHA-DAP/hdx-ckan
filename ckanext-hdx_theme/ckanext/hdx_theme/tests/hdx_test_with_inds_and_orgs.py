'''
Created on Nov 12, 2014

@author: alexandru-m-g
'''
import pylons.config as config

import ckan.plugins.toolkit as tk
import ckan.model as model

import ckanext.hdx_theme.tests.hdx_test_base as hdx_test_base


def get_packages():
    packages = [
        {
            "package_creator": "test function",
            "private": False,
            "dataset_date": "01/01/1960-12/31/2012",
            "indicator": "1",
            "caveats": "These are the caveats",
            "license_other": "TEST OTHER LICENSE",
            "methodology": "This is a test methodology",
            "dataset_source": "World Bank",
            "license_id": "hdx-other",
            "name": "test_indicator_1",
            "notes": "This is a hdxtest indicator",
            "title": "Test Indicator 1",
            "indicator": 1,
            "groups": [{"name": "roger"}]
        },
        {
            "package_creator": "test function",
            "indicator": "1",
            "private": False,
            "dataset_date": "01/01/1960-12/31/2012",
            "caveats": "These are the caveats",
            "license_other": "TEST OTHER LICENSE",
            "methodology": "This is a test methodology",
            "dataset_source": "World Bank",
            "license_id": "hdx-other",
            "name": "test_indicator_2",
            "notes": "This is a hdxtest indicator 2",
            "title": "Test Indicator 2",
            "groups": [{"name": "roger"}]
        },
        {
            "package_creator": "test function",
            "private": False,
            "dataset_date": "01/01/1960-12/31/2012",
            "caveats": "These are the caveats",
            "license_other": "TEST OTHER LICENSE",
            "methodology": "This is a test methodology",
            "dataset_source": "World Bank",
            "license_id": "hdx-other",
            "name": "test_dataset_1",
            "notes": "This is a hdxtest dataset 1",
            "title": "Test Dataset 1",
            "groups": [{"name": "roger"}]
        },
        {
            "package_creator": "test function",
            "private": True,
            "dataset_date": "01/01/1960-12/31/2012",
            "indicator": "1",
            "caveats": "These are the caveats for private dataset",
            "license_other": "TEST OTHER LICENSE",
            "methodology": "This is a test methodology",
            "dataset_source": "World Bank",
            "license_id": "hdx-other",
            "name": "test_private_dataset_1",
            "notes": "This is a private test dataset",
            "title": "Test Private dataset 1",
            "indicator": 1,
            "groups": [{"name": "roger"}],
            "owner_org": "hdx-test-org",
        }
    ]
    return packages


def get_organization():
    organization = {'name': 'hdx-test-org',
                    'title': 'Hdx Test Org', 'users': [{'name': 'testsysadmin'}]}
    return organization


def get_resource():
    resource = {
        'package_id': 'test_private_dataset_1',
        'url': config.get('ckan.site_url', '') + '/storage/f/test_folder/hdx_test.csv',
        'resource_type': 'file.upload',
        'format': 'CSV',
        'name': 'hdx_test.csv'
    }
    return resource


class HDXWithIndsAndOrgsTest(hdx_test_base.HdxBaseTest):

    @classmethod
    def _load_plugins(cls):
        hdx_test_base.load_plugin('hdx_package hdx_theme')

    @classmethod
    def _get_action(cls, action_name):
        return tk.get_action(action_name)

    @classmethod
    def _create_test_data(cls):
        super(HDXWithIndsAndOrgsTest, cls)._create_test_data()

        packages = get_packages()
        organization = get_organization()
        resource = get_resource()

        context = {'ignore_auth': True,
                   'model': model, 'session': model.Session, 'user': 'testsysadmin'}

        cls._get_action('organization_create')(context, organization)

        for package in packages:
            c = {'ignore_auth': True,
                 'model': model, 'session': model.Session, 'user': 'testsysadmin'}
            cls._get_action('package_create')(c, package)
            # This is a copy of the hack done in dataset_controller
            cls._get_action('package_update')(c, package)

        cls._get_action('resource_create')(context, resource)
