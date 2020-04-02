import ckan.model as model

from ckan.tests import factories

import ckanext.hdx_theme.tests.hdx_test_with_inds_and_orgs as hdx_test_with_inds_and_orgs

from ckanext.hdx_package.helpers.constants import COD_ENDORSED, COD_NOT, COD_CANDIDATE
from ckanext.hdx_users.helpers.permissions import Permissions


class TestCod(hdx_test_with_inds_and_orgs.HDXWithIndsAndOrgsTest):

    @classmethod
    def setup_class(cls):
        super(TestCod, cls).setup_class()

        context_sysadmin = {'model': model, 'session': model.Session, 'user': 'testsysadmin'}

        factories.User(name='editor_user', email='editor_user@example.com')
        cls._get_action('organization_member_create')(context_sysadmin,
                                                       {'id': 'hdx-test-org',
                                                        'username': 'editor_user',
                                                        'role': 'editor'})

        factories.User(name='cod_user', email='cod_user@example.com')
        cls._get_action('organization_member_create')(context_sysadmin,
                                                      {'id': 'hdx-test-org',
                                                       'username': 'cod_user',
                                                       'role': 'editor'})

        Permissions('cod_user').set_permissions(context_sysadmin, [Permissions.PERMISSION_MANAGE_COD])

    def test_cod_update(self):
        '''
        Tests that only a user with cod update rights or a sysadmin can update the cod field
        '''
        context = {'model': model, 'session': model.Session, 'user': 'editor_user'}
        context_sysadmin = {'model': model, 'session': model.Session, 'user': 'testsysadmin'}
        context_cod_user = {'model': model, 'session': model.Session, 'user': 'cod_user'}

        dataset_dict = self.__change_cod_field(context_sysadmin, COD_CANDIDATE)
        assert dataset_dict.get('cod_level') == COD_CANDIDATE

        dataset_dict = self.__change_cod_field(context_sysadmin, COD_ENDORSED)
        assert dataset_dict.get('cod_level') == COD_ENDORSED

        dataset_dict = self.__change_cod_field(context, COD_NOT)
        assert dataset_dict.get('cod_level') == COD_ENDORSED, 'Normal editors shouldn\'t be allowed to change COD'

        dataset_dict = self.__change_cod_field(context_cod_user, COD_CANDIDATE)
        assert dataset_dict.get('cod_level') == COD_CANDIDATE

    def __change_cod_field(self, context, cod_value):
        return self._get_action('package_patch')(context,
                                                 {
                                                     'id': 'test_dataset_1',
                                                     'cod_level': cod_value
                                                 })

