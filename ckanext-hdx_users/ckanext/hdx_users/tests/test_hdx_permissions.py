import logging

import ckanext.hdx_theme.tests.hdx_test_base as hdx_test_base
import ckanext.hdx_users.helpers.permissions as permissions

log = logging.getLogger(__name__)


class TestHdxPermissions(hdx_test_base.HdxBaseTest):

    def test_permission_save(self):
        permissions.set_permissions(
            {'user': 'testsysadmin'},
            'tester',
            [permissions.MANAGE_CRISIS_PERMISSION, permissions.MANAGE_COD_PERMISSION]
        )
