import ckan.tests.factories as factories
import ckan.model as model
import ckan.plugins.toolkit as tk

import ckanext.hdx_theme.tests.hdx_test_base as hdx_test_base

from ckanext.hdx_org_group.helpers.static_lists import ORGANIZATION_TYPE_LIST

config = tk.config


class TestQuarantine(hdx_test_base.HdxBaseTest):

    NORMAL_USER = 'quarantine_user'
    SYSADMIN_USER = 'testsysadmin'
    PACKAGE_ID = 'test_dataset_4_quarantine'

    @classmethod
    def _get_action(cls, action_name):
        return tk.get_action(action_name)

    @classmethod
    def setup_class(cls):
        super(TestQuarantine, cls).setup_class()
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

        context = {'model': model, 'session': model.Session, 'user': cls.NORMAL_USER}
        cls._get_action('package_create')(context, package)

    def test_normal_user_cannot_modify_quarantine(self):
        package_dict = self._get_action('package_show')({}, {'id': self.PACKAGE_ID})
        resource_id = package_dict['resources'][0]['id']

        package_dict = self._change_quarantine_flag(resource_id, True, self.SYSADMIN_USER)
        assert package_dict['resources'][0]['in_quarantine'] is True

        package_dict = self._change_quarantine_flag(resource_id, False, self.NORMAL_USER)
        assert package_dict['resources'][0]['in_quarantine'] is True

        package_dict = self._change_quarantine_flag(resource_id, False, self.SYSADMIN_USER)
        assert package_dict['resources'][0]['in_quarantine'] is False

    def _change_quarantine_flag(self, resource_id, in_quarantine, username):
        self._get_action('resource_patch')(
            {
                'model': model, 'session': model.Session,
                'user': username,
            },
            {'id': resource_id, 'in_quarantine': in_quarantine}
        )
        return self._get_action('package_show')({}, {'id': self.PACKAGE_ID})

