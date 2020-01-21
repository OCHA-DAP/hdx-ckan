import datetime

import ckan.model as model

from ckan.tests import factories

import ckanext.hdx_theme.tests.hdx_test_with_inds_and_orgs as hdx_test_with_inds_and_orgs


class TestSpecialFieldsInPkg(hdx_test_with_inds_and_orgs.HDXWithIndsAndOrgsTest):

    def test_updated_by_script(self):
        context = {'model': model, 'session': model.Session, 'user': 'editor_user'}
        context_sysadmin = {'model': model, 'session': model.Session, 'user': 'testsysadmin'}

        editor_user = factories.User(name='editor_user', email='editor_user@example.com')

        self._get_action('organization_member_create')(context_sysadmin,
                                                       {'id': 'hdx-test-org', 'username': 'editor_user',
                                                        'role': 'editor'})

        self._get_action('package_patch')(context,
                                          {
                                              'id': 'test_dataset_1',
                                              'updated_by_script': 'HDX Nose Tests'
                                          })
        dataset_dict = self._get_action('package_patch')(context,
                                                         {
                                                             'id': 'test_dataset_1',
                                                             'updated_by_script': 'HDX Nose Tests'
                                                         })
        assert dataset_dict.get('updated_by_script') == 'HDX Nose Tests'

        dataset_dict = self._get_action('package_patch')(context,
                                                         {
                                                             'id': 'test_dataset_1',
                                                             'updated_by_script': ''
                                                         })
        assert dataset_dict.get('updated_by_script') is None
