import ckan.tests.factories as factories
import ckan.model as model
import ckan.plugins.toolkit as tk

import ckanext.hdx_theme.tests.hdx_test_base as hdx_test_base

from ckanext.hdx_org_group.helpers.static_lists import ORGANIZATION_TYPE_LIST

config = tk.config
NotAuthorized = tk.NotAuthorized


class TestQAChecklist(hdx_test_base.HdxBaseTest):

    NORMAL_USER = 'qa_checklist_completed_user'
    SYSADMIN_USER = 'testsysadmin'
    PACKAGE_ID = 'test_dataset_4_qa_checklist'
    PACKAGE_ID2 = 'test_dataset_4_qa_checklist_2'
    CHECKLIST_DICT = {
        "version": 1,
        "metadata": {"m13": True, "m12": True, "m15": True},
        "resources": [
            {"r5": True, "r6": True, "r7": True}
        ],
        "dataProtection": {"dp5": True, "dp4": True, "dp3": True}
    }

    RESOURCE_ID = None
    RESOURCE_ID2 = None

    @classmethod
    def _get_action(cls, action_name):
        return tk.get_action(action_name)

    @classmethod
    def setup_class(cls):
        super(TestQAChecklist, cls).setup_class()
        factories.User(name=cls.NORMAL_USER, email='qa_checklist_completed_user@hdx.hdxtest.org')
        factories.Organization(
            name='org_name_4_qa_checklist',
            title='ORG NAME FOR QA CHECKLIST',
            users=[
                {'name': cls.NORMAL_USER, 'capacity': 'admin'},
            ],
            hdx_org_type=ORGANIZATION_TYPE_LIST[0][1],
            org_url='https://hdx.hdxtest.org/'
        )
        dataset_dict = cls.create_packages_by_user(cls.PACKAGE_ID, cls.NORMAL_USER, True)
        cls.RESOURCE_ID = dataset_dict['resources'][0]['id']

        dataset_dict2 = cls.create_packages_by_user(cls.PACKAGE_ID2, cls.NORMAL_USER, False)
        cls.RESOURCE_ID2 = dataset_dict2['resources'][0]['id']

    @classmethod
    def create_packages_by_user(cls, pkg_id, user, qa_checklist):
        package = {
            "package_creator": "test function",
            "private": False,
            "dataset_date": "01/01/1960-12/31/2012",
            "caveats": "These are the caveats",
            "license_other": "TEST OTHER LICENSE",
            "methodology": "This is a test methodology",
            "dataset_source": "Test data",
            "license_id": "hdx-other",
            "name": pkg_id,
            "notes": "This is a test dataset",
            "title": "Test Dataset for QA Checklist " + pkg_id,
            "owner_org": "org_name_4_qa_checklist",
            "groups": [{"name": "roger"}],
            "resources": [
                {
                    'package_id': pkg_id,
                    'url': config.get('ckan.site_url', '') + '/storage/f/test_folder/hdx_test.csv',
                    'resource_type': 'file.upload',
                    'format': 'CSV',
                    'name': 'hdx_test.csv'
                },
                {
                    'package_id': pkg_id,
                    'url': config.get('ckan.site_url', '') + '/storage/f/test_folder/hdx_test.csv',
                    'resource_type': 'file.upload',
                    'format': 'CSV',
                    'name': 'hdx_test2.csv'
                }
            ]
        }
        if qa_checklist:
            package['qa_checklist'] = '{"test": "test"}'
        context = {'model': model, 'session': model.Session, 'user': user}
        return cls._get_action('package_create')(context, package)

    def test_qa_checklist_not_on_dataset_creation(self):
        '''
        Tests that qa_checklist cannot be set on dataset creation / package_create()
        '''

        package_dict = self._get_action('package_show')({}, {'id': self.PACKAGE_ID})

        assert "qa_checklist" not in package_dict
        for resource_dict in package_dict.get('resources'):
            assert "qa_checklist" not in resource_dict
            assert "qa_checklist_num" not in resource_dict

    def test_qa_checklist_not_reset_after_update(self):
        '''
        Tests that qa_checklist doesn't get reset by a normal dataset_update
        '''

        self._qa_checklist_update(self.PACKAGE_ID, self.RESOURCE_ID, self.SYSADMIN_USER)
        self._verify_checklist(self.PACKAGE_ID)

        self._change_description_of_package(self.PACKAGE_ID, self.NORMAL_USER)
        self._verify_checklist(self.PACKAGE_ID)
        self._change_description_of_package(self.PACKAGE_ID, self.SYSADMIN_USER,
                                            new_description='modified by sysadmin for qa checklist')
        self._verify_checklist(self.PACKAGE_ID)

    def test_qa_checklist_reset_on_empty_checklist_push(self):
        '''
        Tests that qa_checklist gets reset when pushing empty checklist data
        '''
        self._qa_checklist_update(self.PACKAGE_ID, self.RESOURCE_ID, self.SYSADMIN_USER)
        self._verify_checklist(self.PACKAGE_ID)
        empty_checklist = {
            "version": 1,
            "resources": [
                {}
            ],
            "dataProtection": {},
            "metadata": {}
        }

        self._qa_checklist_update(self.PACKAGE_ID, self.RESOURCE_ID, self.SYSADMIN_USER, data_dict=empty_checklist)
        package_dict = self._get_action('package_show')({}, {'id': self.PACKAGE_ID})
        assert "qa_checklist" not in package_dict
        for resource_dict in package_dict.get('resources'):
            assert "qa_checklist" not in resource_dict
            assert "qa_checklist_num" not in resource_dict

    def test_resource_qa_checklist_on_resource_delete(self):
        '''
        Tests that qa_checklist at the resource level gets deleted when the resource is deleted
        '''

        self._qa_checklist_update(self.PACKAGE_ID2, self.RESOURCE_ID2, self.SYSADMIN_USER)
        self._verify_checklist(self.PACKAGE_ID2)

        context = {'model': model, 'session': model.Session, 'user': self.NORMAL_USER}
        self._get_action('resource_delete')(context, {'id': self.RESOURCE_ID2})
        checklist = self._get_action('hdx_package_qa_checklist_show')({}, {'id': self.PACKAGE_ID2})
        assert checklist.get('resources') != self.CHECKLIST_DICT.get('resources')
        assert checklist.get('dataProtection') == self.CHECKLIST_DICT.get('dataProtection')
        assert checklist.get('metadata') == self.CHECKLIST_DICT.get('metadata')

    def _verify_checklist(self, package_id):
        checklist = self._get_action('hdx_package_qa_checklist_show')({}, {'id': package_id})
        for resource_info in checklist.get('resources'):
            resource_info.pop('id', None)
        assert checklist.get('resources') == self.CHECKLIST_DICT.get('resources')
        assert checklist.get('dataProtection') == self.CHECKLIST_DICT.get('dataProtection')
        assert checklist.get('metadata') == self.CHECKLIST_DICT.get('metadata')

    def _qa_checklist_update(self, package_id, resource_id, user, data_dict=None):
        context = {'model': model, 'session': model.Session, 'user': user}

        d = {
            "id": package_id,
        }
        if data_dict is None:
            d.update(self.CHECKLIST_DICT)
        else:
            d.update(data_dict)
        d['resources'][0]['id'] = resource_id

        return self._get_action('hdx_package_qa_checklist_update')(context, d)

    def _change_description_of_package(self, package_id, user, new_description='modified for qa checklist'):
        context = {'model': model, 'session': model.Session, 'user': user}
        return self._get_action('package_patch')(context, {'id': package_id, 'notes': new_description})
