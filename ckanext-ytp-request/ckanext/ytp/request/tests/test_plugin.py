import paste.fixture
import pylons.test
from ckan.tests import TestCase
from ckan.logic import NotFound
from ckan import model, plugins
from ckan.plugins import toolkit
from ckanext.ytp.request.tools import get_organization_admins


class TestYtpRequestPlugin(TestCase):
    """ Test YtpOrganizationPlugin class """

    @classmethod
    def setup_class(cls):
        cls.app = paste.fixture.TestApp(pylons.test.pylonsapp)

    def setup(self):
        self.sysadmin = model.User(name='test_sysadmin', sysadmin=True)
        model.Session.add(self.sysadmin)
        model.Session.commit()
        model.Session.remove()

    def teardown(self):
        model.repo.rebuild_db()

    @classmethod
    def teardown_class(cls):
        pass

    def _create_context(self):
        context = {'model': model, 'session': model.Session, 'ignore_auth': True}
        admin_user = plugins.toolkit.get_action('get_site_user')(context, None)
        context['user'] = admin_user['name']
        return context

    def _create_user(self, name):
        user = model.User(name=name)
        model.Session.add(user)
        model.Session.commit()
        return user

    def test_member_request_create(self):
        context = self._create_context()
        admin_context = self._create_context()
        self._create_user("tester")
        context['user'] = "tester"

        self.assert_raises(NotFound, toolkit.get_action("member_request_create"), context, {"group": "test_organization", 'role': "editor"})
        toolkit.get_action("organization_create")(admin_context, {"name": "test_organization"})
        self.assert_len(toolkit.get_action("member_request_list")(admin_context, {"group": "test_organization"}), 0)

        toolkit.get_action("member_request_create")(context, {"group": "test_organization", 'role': "editor"})
        self.assert_len(toolkit.get_action("member_request_list")(admin_context, {"group": "test_organization"}), 1)

    def test_member_request_process(self):
        context_user = self._create_context()
        self._create_user("process_tester")
        context_user['user'] = "process_tester"

        context_admin = self._create_context()

        for organization, approve, result in ('test_process_approve', True, "active"), ('test_process_reject', False, "deleted"):
            toolkit.get_action("organization_create")(context_admin, {"name": organization})

            member = toolkit.get_action("member_request_create")(context_user, {"group": organization, 'role': "editor"})
            show_member = toolkit.get_action("member_request_show")(context_user, {"member": member['id']})
            self.assert_equal(show_member['state'], "pending")

            toolkit.get_action("member_request_process")(context_admin, {"member": member['id'], "approve": approve})
            show_member = toolkit.get_action("member_request_show")(context_user, {"member": member['id']})
            self.assert_equal(show_member['state'], result)

    def test_get_organization_admins(self):
        context_user = self._create_context()
        user = self._create_user("test_admins_1")
        context_user['user'] = "test_admins_1"

        context_user_2 = self._create_context()
        user_2 = self._create_user("test_admins_2")
        context_user_2['user'] = "test_admins_2"

        context_admin = self._create_context()

        organization = toolkit.get_action("organization_create")(context_admin, {"name": 'test_admins'})

        for admin in get_organization_admins(organization['id']):
            self.assert_true(admin.id != user.id)

        member = toolkit.get_action("member_request_create")(context_user, {"group": organization['id'], 'role': "editor"})
        toolkit.get_action("member_request_process")(context_admin, {"member": member['id'], "approve": False})

        for admin in get_organization_admins(organization['id']):
            self.assert_true(admin.id != user.id)

        member = toolkit.get_action("member_request_create")(context_user, {"group": organization['id'], 'role': "editor"})
        toolkit.get_action("member_request_process")(context_admin, {"member": member['id'], "approve": True})

        for admin in get_organization_admins(organization['id']):
            self.assert_true(admin.id != user.id)

        member = toolkit.get_action("member_request_create")(context_user_2, {"group": organization['id'], 'role': "admin"})
        toolkit.get_action("member_request_process")(context_admin, {"member": member['id'], "approve": True})

        ok = False
        for admin in get_organization_admins(organization['id']):
            if admin.id == user_2.id:
                ok = True

        if not ok:
            self.fail("User not found from organization admins")
