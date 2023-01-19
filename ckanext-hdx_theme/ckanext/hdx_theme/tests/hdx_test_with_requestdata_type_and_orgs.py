'''
Created on Nov 12, 2014

@author: alexandru-m-g
'''
import ckan.plugins.toolkit as tk
import ckan.model as model

import ckanext.hdx_theme.tests.hdx_test_base as hdx_test_base

from ckanext.hdx_org_group.helpers.static_lists import ORGANIZATION_TYPE_LIST

config = tk.config


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
            "name": "test_activity_request_data_1",
            "notes": "This is a test activity 1",
            "title": "Test Activity 1 request data",
            "owner_org": "hdx-test-org",
            "groups": [{"name": "roger"}],
            "is_requestdata_type": True,
            "file_types": ["csv"],
            "field_names": ["field1", "field2"]
        },
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
            "name": "test_activity_request_data_2",
            "notes": "This is a test activity 2",
            "title": "Test Activity 2 request data",
            "owner_org": "hdx-test-org",
            "groups": [{"name": "roger"}],
            "is_requestdata_type": True,
            "file_types": ["csv"],
            "field_names": ["field1", "field2"]
        },
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
            "name": "test_activity_request_data_3",
            "notes": "This is a test activity 3",
            "title": "Test Activity 3 request data",
            "owner_org": "hdx-test-org",
            "groups": [{"name": "roger"}],
            "is_requestdata_type": True,
            "file_types": ["csv"],
            "field_names": ["field1", "field2"]
        },
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
            "name": "test_activity_request_data_4",
            "notes": "This is a test activity 4",
            "title": "Test Activity 4 request data",
            "owner_org": "hdx-test-org",
            "groups": [{"name": "roger"}],
            "is_requestdata_type": True,
            "file_types": ["csv"],
            "field_names": ["field1", "field2"]
        },
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
            "name": "test_activity_request_data_5",
            "notes": "This is a test activity 5",
            "title": "Test Activity 5 request data",
            "owner_org": "hdx-test-org",
            "groups": [{"name": "roger"}],
            "is_requestdata_type": True,
            "file_types": ["csv"],
            "field_names": ["field1", "field2"]
        },
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
            "name": "test_activity_request_data_6",
            "notes": "This is a test activity 6",
            "title": "Test Activity 6 request data",
            "owner_org": "hdx-test-org",
            "groups": [{"name": "roger"}],
            "is_requestdata_type": True,
            "file_types": ["csv"],
            "field_names": ["field1", "field2"]
        },
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
            "name": "test_activity_request_data_7",
            "notes": "This is a test activity 7",
            "title": "Test Activity 7 request data",
            "owner_org": "hdx-test-org",
            "groups": [{"name": "roger"}],
            "is_requestdata_type": True,
            "file_types": ["csv"],
            "field_names": ["field1", "field2"]
        },
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
            "name": "test_activity_request_data_8",
            "notes": "This is a test activity 8",
            "title": "Test Activity 8 request data",
            "owner_org": "hdx-test-org",
            "groups": [{"name": "roger"}],
            "is_requestdata_type": True,
            "file_types": ["csv"],
            "field_names": ["field1", "field2"]
        },
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
            "name": "test_activity_request_data_9",
            "notes": "This is a test activity 9",
            "title": "Test Activity 9 request data",
            "owner_org": "hdx-test-org",
            "groups": [{"name": "roger"}],
            "is_requestdata_type": True,
            "file_types": ["csv"],
            "field_names": ["field1", "field2"]
        },
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
            "name": "test_activity_request_data_10",
            "notes": "This is a test activity 10",
            "title": "Test Activity 10 request data",
            "owner_org": "hdx-test-org",
            "groups": [{"name": "roger"}],
            "is_requestdata_type": True,
            "file_types": ["csv"],
            "field_names": ["field1", "field2"]
        },
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
            "name": "test_activity_request_data_11",
            "notes": "This is a test activity 11",
            "title": "Test Activity 11 request data",
            "owner_org": "hdx-test-org",
            "groups": [{"name": "roger"}],
            "is_requestdata_type": True,
            "file_types": ["csv"],
            "field_names": ["field1", "field2"]
        },
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
            "name": "test_activity_request_data_12",
            "notes": "This is a test activity 12",
            "title": "Test Activity 12 request data",
            "owner_org": "hdx-test-org",
            "groups": [{"name": "roger"}],
            "is_requestdata_type": True,
            "file_types": ["csv"],
            "field_names": ["field1", "field2"]
        }
    ]
    return packages


def get_organization():
    organization = {'name': 'hdx-test-org',
                    'title': 'Hdx Test Org',
                    'hdx_org_type': ORGANIZATION_TYPE_LIST[0][1],
                    'org_acronym': 'HTO',
                    'org_url': 'http://test-org.test',
                    'description': 'This is a test organization',
                    'users': [{'name': 'testsysadmin', 'capacity': 'admin'}, {'name': 'tester', 'capacity': 'member'}]}
    return organization


# def get_resource():
#     resource = {
#         'package_id': 'test_private_dataset_1',
#         'url': config.get('ckan.site_url', '') + '/storage/f/test_folder/hdx_test.csv',
#         'resource_type': 'file.upload',
#         'format': 'CSV',
#         'name': 'hdx_test.csv'
#     }
#     return resource


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


class HDXWithRequestdataTypeAndOrgsTest(hdx_test_base.HdxBaseTest):
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
        super(HDXWithRequestdataTypeAndOrgsTest, cls)._create_test_data()

        packages = get_packages()
        organization = get_organization()
        # resource = get_resource()
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

            # cls._get_action('resource_create')(context, resource)
