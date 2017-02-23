'''
Created on Aug 25, 2015

@author: alexandru-m-g
'''

import logging as logging
import ckan.plugins.toolkit as tk
import ckan.model as model
import ckan.logic as logic

import ckanext.hdx_theme.tests.hdx_test_base as hdx_test_base
import ckanext.hdx_users.model as umodel
import ckanext.hdx_user_extra.model as ue_model
import ckanext.hdx_package.helpers.caching as caching

log = logging.getLogger(__name__)


class TestHDXPackageCreate(hdx_test_base.HdxBaseTest):
    @classmethod
    def _load_plugins(cls):
        hdx_test_base.load_plugin('hdx_package hdx_theme')

    @classmethod
    def _get_action(cls, action_name):
        return tk.get_action(action_name)

    @classmethod
    def setup_class(cls):
        super(TestHDXPackageCreate, cls).setup_class()
        umodel.setup()
        ue_model.create_table()

    def test_create_with_group(self):
        package = {
            "package_creator": "test function",
            "private": False,
            "dataset_date": "01/01/1960-12/31/2012",
            "indicator": "1",
            "caveats": "These are the caveats",
            "license_other": "TEST OTHER LICENSE",
            "methodology": "This is a test methodology",
            "dataset_source": "World Bank",
            "license_id": "hdx-other",
            "name": "test_activity_3",
            "notes": "This is a test activity",
            "title": "Test Activity 3",
        }

        context = {'ignore_auth': True,
                   'model': model, 'session': model.Session, 'user': 'nouser'}

        try:
            self._get_action('package_create')(context, package)
            assert False, 'It should not be possible to create a package without group'
        except logic.ValidationError:
            assert True, 'It should not be possible to create a package without group'

        try:
            package['groups'] = [{"name": "ROGER"}]
            self._get_action('package_create')(context, package)
            assert False, 'It should not be possible to create a package with a wrong group name'
        except logic.ValidationError:
            assert True, 'It should not be possible to create a package with a wrong group name'

        try:
            package['name'] += 'with_group_by_name'
            package['title'] += 'with group by name'
            package['groups'] = [{"name": "roger"}]
            self._get_action('package_create')(context, package)
            assert True
        except logic.ValidationError:
            assert False

    def test_create_with_2_groups(self):
        package = {
            "package_creator": "test function",
            "private": False,
            "dataset_date": "01/01/1960-12/31/2012",
            "indicator": "1",
            "caveats": "These are the caveats",
            "license_other": "TEST OTHER LICENSE",
            "methodology": "This is a test methodology",
            "dataset_source": "World Bank",
            "license_id": "hdx-other",
            "name": "test_activity_3_with_2_groups",
            "notes": "This is a test activity",
            "title": "Test Activity 3 with 2 Groups",
        }

        context = {'ignore_auth': True,
                   'model': model, 'session': model.Session, 'user': 'testsysadmin'}

        group_list = caching.cached_group_list()

        try:
            package['groups'] = [{"id": group_list[0]['id']}, {"name": 'non-existing name'}]
            self._get_action('package_create')(context, package)
            assert False
        except logic.ValidationError:
            assert True

        try:
            package['groups'] = [{"id": group_list[0]['id']}, {"name": group_list[1]['name']}]
            self._get_action('package_create')(context, package)
            data_dict = self._get_action('package_show')(context, {"id": "test_activity_3_with_2_groups"})
            assert len(data_dict.get('groups', [])) == 2
        except logic.ValidationError:
            assert False
