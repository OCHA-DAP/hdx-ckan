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
            "groups": [{"name": "roger"}],
            "owner_org": "hdx-test-org",
        }
    ]
    return packages


def get_organization():
    organization = {'name': 'hdx-test-org',
                    'title': 'Hdx Test Org',
                    'org_url': 'http://test-org.test',
                    'description': 'This is a test organization',
                    'users': [{'name': 'testsysadmin'}]}
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


def get_users():
    new_users = [
        {
            'name': 'johndoe1',
            'fullname': 'John Doe1',
            'email': 'johndoe1@test.test',
            'password': 'password',
            'about': 'John Doe1, 1st user created by HDXWithIndsAndOrgsTest. Member of hdx-test-org.'
        },
        {
            'name': 'annaanderson2',
            'fullname': 'Anna Anderson2',
            'email': 'annaanderson2@test.test',
            'password': 'password',
            'about': 'Anna Anderson2, 2nd user created by HDXWithIndsAndOrgsTest. Member of hdx-test-org.'
        },
        {
            'name': 'janedoe3',
            'fullname': 'Jane Doe3',
            'email': 'janedoe3@test.test',
            'password': 'password',
            'about': 'Jane Doe3, 3rd user created by HDXWithIndsAndOrgsTest. Member of hdx-test-org.'
        }

    ]
    return new_users


class HDXWithIndsAndOrgsTest(hdx_test_base.HdxBaseTest):
    '''
    This class extends the HDX Base test class by adding additional test data.
    More precisely: datasets, organizations, members to organizations
    '''

    @classmethod
    def _load_plugins(cls):
        hdx_test_base.load_plugin('hdx_package hdx_theme')

    @classmethod
    def _get_action(cls, action_name):
        return tk.get_action(action_name)

    @classmethod
    def _create_test_data(cls, create_datasets=True, create_members=False):
        '''
        This method is responsible for creating additional test data.
        Please note that the corresponding function from the parent is still called
        so all standard test data will still be available to the tests.

        Override this function in your test and call it with different params
        depending on what test data you need.

        :param create_datasets: If the org doesn't need datasets set this flag to False. Default True.
        :type create_datasets: boolean
        :param create_members: If the org should have some members set this flag to True. Default False.
            Note that 'testsysadmin' will be a member (admin) of the org regardless of the flag.
        :type create_members: boolean

        '''
        super(HDXWithIndsAndOrgsTest, cls)._create_test_data()

        packages = get_packages()
        organization = get_organization()
        resource = get_resource()
        users = get_users()

        if create_members:
            organization['users'] = []
            for new_user in users:
                context = {'ignore_auth': True,
                           'model': model, 'session': model.Session, 'user': 'testsysadmin'}
                user = cls._get_action('user_create')(context, new_user)
                member = {'name': user['id'], 'capacity': 'member'}
                organization['users'].append(member)

        context = {'ignore_auth': True,
                   'model': model, 'session': model.Session, 'user': 'testsysadmin'}

        cls._get_action('organization_create')(context, organization)

        if create_datasets:
            for package in packages:
                c = {'ignore_auth': True,
                     'model': model, 'session': model.Session, 'user': 'testsysadmin'}
                cls._get_action('package_create')(c, package)
                # This is a copy of the hack done in dataset_controller
                cls._get_action('package_update')(c, package)

            cls._get_action('resource_create')(context, resource)
