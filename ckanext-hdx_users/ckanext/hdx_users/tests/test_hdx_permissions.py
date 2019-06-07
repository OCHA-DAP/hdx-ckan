import logging

import ckan.plugins.toolkit as tk

import ckanext.hdx_theme.tests.hdx_test_base as hdx_test_base
from ckanext.hdx_users.helpers.permissions import Permissions

log = logging.getLogger(__name__)
NotAuthorized = tk.NotAuthorized


class TestHdxPermissions(hdx_test_base.HdxBaseTest):

    def test_permission_save(self):
        first_list = [Permissions.PERMISSION_MANAGE_CRISIS, Permissions.PERMISSION_MANAGE_COD]
        second_list = [Permissions.PERMISSION_VIEW_REQUEST_DATA, Permissions.PERMISSION_MANAGE_CRISIS, Permissions.PERMISSION_MANAGE_COD]

        permissions = Permissions('tester')

        permissions.set_permissions(
            {'user': 'testsysadmin'},
            first_list
        )

        loaded_list1 = permissions.get_permission_list()
        assert first_list == loaded_list1

        permissions.set_permissions(
            {'user': 'testsysadmin'},
            second_list
        )
        loaded_list2 = permissions.get_permission_list()
        assert second_list == loaded_list2

        try:
            permissions.set_permissions(
                {'user': 'tester'},
                second_list
            )
            assert False
        except NotAuthorized as e:
            assert True

