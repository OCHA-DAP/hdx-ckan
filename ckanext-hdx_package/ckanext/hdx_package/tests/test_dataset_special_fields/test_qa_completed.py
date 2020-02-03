import ckan.tests.factories as factories
import ckan.model as model
import ckan.plugins.toolkit as tk

import ckanext.hdx_theme.tests.hdx_test_base as hdx_test_base

from ckanext.hdx_org_group.helpers.static_lists import ORGANIZATION_TYPE_LIST

config = tk.config
NotAuthorized = tk.NotAuthorized

class TestQACompleted(hdx_test_base.HdxBaseTest):

    NORMAL_USER = 'qa_completed_user'
    SYSADMIN_USER = 'testsysadmin'
    PACKAGE_ID = 'test_dataset_4_qa_completed'
    PACKAGE_ID_2 = 'test_dataset_4_qa_completed_2'
    PACKAGE_ID_3 = 'test_dataset_4_qa_completed_3'
    PACKAGE_ID_4 = 'test_dataset_4_qa_completed_4'

    @classmethod
    def _get_action(cls, action_name):
        return tk.get_action(action_name)

    @classmethod
    def setup_class(cls):
        super(TestQACompleted, cls).setup_class()
        factories.User(name=cls.NORMAL_USER, email='qa_completed_user@hdx.hdxtest.org')
        factories.Organization(
            name='org_name_4_qa_completed',
            title='ORG NAME FOR QA COMPLETED',
            users=[
                {'name': cls.NORMAL_USER, 'capacity': 'admin'},
            ],
            hdx_org_type=ORGANIZATION_TYPE_LIST[0][1],
            org_url='https://hdx.hdxtest.org/'
        )
        cls.create_packages_by_user(cls.PACKAGE_ID, cls.NORMAL_USER)
        cls.create_packages_by_user(cls.PACKAGE_ID_2, cls.NORMAL_USER, True)
        cls.create_packages_by_user(cls.PACKAGE_ID_3, cls.SYSADMIN_USER)
        cls.create_packages_by_user(cls.PACKAGE_ID_4, cls.SYSADMIN_USER, True)

    @classmethod
    def create_packages_by_user(cls, pkg_id, user, qa_completed=None):
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
            "title": "Test Dataset for QA Completed " + pkg_id,
            "owner_org": "org_name_4_qa_completed",
            "groups": [{"name": "roger"}],
            "resources": [
                {
                    'package_id': pkg_id,
                    'url': config.get('ckan.site_url', '') + '/storage/f/test_folder/hdx_test.csv',
                    'resource_type': 'file.upload',
                    'format': 'CSV',
                    'name': 'hdx_test.csv'
                }
            ]
        }
        if qa_completed:
            package['qa_completed'] = qa_completed
        context = {'model': model, 'session': model.Session, 'user':user}
        cls._get_action('package_create')(context, package)

    def test_qa_completed_not_on_dataset_creation(self):
        '''
        Tests that qa_completed cannot be set on dataset creation / package_create()
        '''

        package_dict = self._get_action('package_show')({}, {'id': self.PACKAGE_ID})
        package_dict_2 = self._get_action('package_show')({}, {'id': self.PACKAGE_ID_2})
        package_dict_3 = self._get_action('package_show')({}, {'id': self.PACKAGE_ID_3})
        package_dict_4 = self._get_action('package_show')({}, {'id': self.PACKAGE_ID_4})

        assert "qa_completed" in package_dict and package_dict.get("qa_completed") is False
        assert "qa_completed" in package_dict_2 and package_dict_2.get("qa_completed") is False
        assert "qa_completed" in package_dict_3 and package_dict_3.get("qa_completed") is False
        assert "qa_completed" in package_dict_4 and package_dict_4.get("qa_completed") is False

    def test_qa_completed_not_on_dataset_update(self):
        '''
        Tests that qa_completed cannot be set on dataset creation / package_create()
        '''

        # qa_completed field cannot be set via normal package_patch / package_update
        package_dict = self._package_patch_qa_completed_flag(self.PACKAGE_ID, True, self.NORMAL_USER)
        assert "qa_completed" in package_dict and package_dict.get("qa_completed") is False
        package_dict = self._package_patch_qa_completed_flag(self.PACKAGE_ID, True, self.SYSADMIN_USER)
        assert "qa_completed" in package_dict and package_dict.get("qa_completed") is False

    def test_qa_completed_on_hdx_mark_qa_completed(self):
        '''
        Tests that qa_completed can be changed via hdx_mark_qa_completed() only by sysadmin
        But gets reset when any user changes the dataset.
        '''
        try:
            self._hdx_mark_qa_completed_flag(self.PACKAGE_ID_2, True, self.NORMAL_USER)
            assert False
        except NotAuthorized as e:
            assert True
        package_dict = self._hdx_mark_qa_completed_flag(self.PACKAGE_ID_2, True, self.SYSADMIN_USER)
        assert "qa_completed" in package_dict and package_dict.get("qa_completed") is True
        package_dict = self._change_description_of_package(self.PACKAGE_ID_2, self.NORMAL_USER)
        assert "qa_completed" in package_dict and package_dict.get("qa_completed") is False

        package_dict = self._hdx_mark_qa_completed_flag(self.PACKAGE_ID_3, True, self.SYSADMIN_USER)
        assert "qa_completed" in package_dict and package_dict.get("qa_completed") is True
        package_dict = self._change_description_of_package(self.PACKAGE_ID_3, self.SYSADMIN_USER)
        assert "qa_completed" in package_dict and package_dict.get("qa_completed") is False


    def test_qa_completed_reset_via_hdx_mark_qa_completed(self):
        '''
        Tests that qa_completed can be reset via hdx_mark_qa_completed() only by sysadmin
        '''

        package_dict = self._hdx_mark_qa_completed_flag(self.PACKAGE_ID_4, True, self.SYSADMIN_USER)
        assert "qa_completed" in package_dict and package_dict.get("qa_completed") is True

        package_dict = self._hdx_mark_qa_completed_flag(self.PACKAGE_ID_4, False, self.SYSADMIN_USER)
        assert "qa_completed" in package_dict and package_dict.get("qa_completed") is False

    def _package_patch_qa_completed_flag(self, package_id, qa_completed, user):
        context = {
            'model': model,
            'session': model.Session,
            'user': user
        }
        pkg_dict = {
            "id": package_id,
        }
        if qa_completed is not None:
            pkg_dict["qa_completed"] = qa_completed
        self._get_action('package_patch')(context, pkg_dict)
        return self._get_action('package_show')({}, {'id': package_id})

    def _change_description_of_package(self, package_id, user):
        context = {'model': model, 'session': model.Session, 'user': user}
        return self._get_action('package_patch')(context, {'id': package_id, 'notes': 'modified for qa completed'})

    def _hdx_mark_qa_completed_flag(self, package_id, qa_completed, user):
        context = {'model': model, 'session': model.Session, 'user': user}
        return self._get_action('hdx_mark_qa_completed')(context, {'id': package_id, 'qa_completed': qa_completed})
