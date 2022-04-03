import pytest
import mock

import ckan.lib.search as search
import ckan.model as model
import ckan.plugins.toolkit as tk
import ckan.tests.factories as factories
import ckan.tests.helpers as test_helpers
from ckanext.ytp.request.tools import get_organization_admins
import ckan.logic as logic

_get_action = tk.get_action
config = tk.config
url_for = tk.url_for
NotAuthorized = logic.NotAuthorized
NotFound = logic.NotFound

@pytest.mark.usefixtures("with_request_context")
class TestYtpRequestBase(object):
    def _create_context(self):
        context = {'model': model, 'session': model.Session, 'ignore_auth': True}
        admin_user = _get_action('get_site_user')(context, None)
        context['user'] = admin_user['name']
        return context

    @classmethod
    def _create_user(cls, name, sysadmin=False):
        if sysadmin:
            factories.Sysadmin(name=name)
        else:
            factories.User(name=name)
        model.Session.commit()
        _user = model.User.by_name(name)
        if _user:
            _user.email = name + '@test-domain.com'
            _user.apikey = name + '_apikey'
        model.Session.commit()
        return _user

    dataset1_name = 'sitemap_test_dataset_1'
    dataset2_name = 'sitemap_test_dataset_2'

    dataset1_dict = None  # type: dict
    dataset2_dict = None  # type: dict

    @classmethod
    def setup_class(cls):
        search.clear_all()
        test_helpers.reset_db()
        cls.app = test_helpers._get_test_app()

        sysadmin = 'testsysadmin_ytp'
        sysadmin_user = cls._create_user(sysadmin, True)
        cls.sysadmin_user = {
            'name': sysadmin,
            'apikey': sysadmin_user.apikey
        }

        usr = 'testuser_ytp'
        user = cls._create_user(usr, False)
        cls.sysadmin_user = {
            'name': usr,
            'apikey': user.apikey
        }

        cls.dataset1_dict = cls._create_package(cls.dataset1_name, sysadmin)
        cls.dataset2_dict = cls._create_package(cls.dataset2_name, sysadmin, create_org_and_group=False)

    @classmethod
    def _create_package(cls, pkg_name, user, create_org_and_group=True):
        '''
        :param pkg_name: the name of the new package
        :type pkg_name: str
        :param create_org_and_group: whether to create the org and group for the package. Might've been created already.
        :type create_org_and_group: bool
        :return: id of newly created package
        :rtype: str
        '''
        if create_org_and_group:
            factories.Organization(name='test_owner_org',
                                   org_url='http://example.org/',
                                   hdx_org_type='academic_research',
                                   users=[{'name': 'testsysadmin', 'capacity': 'admin'}]
                                   )
            factories.Group(name='test_group1')
        package = {
            "package_creator": "test function",
            "private": False,
            "dataset_date": "[1960-01-01 TO 2012-12-31]",
            "caveats": "These are the caveats",
            "license_other": "TEST OTHER LICENSE",
            "methodology": "This is a test methodology",
            "dataset_source": "Test data",
            "license_id": "hdx-other",
            "name": pkg_name,
            "notes": "This is a test dataset",
            "title": "Test Dataset for QA Completed " + pkg_name,
            "owner_org": "test_owner_org",
            "groups": [{"name": "test_group1"}],
            "maintainer": user,
            "data_update_frequency": "0",
            "resources": [
                {
                    'package_id': pkg_name,
                    'url': config.get('ckan.site_url', '') + '/storage/f/test_folder/hdx_test.csv',
                    'resource_type': 'file.upload',
                    'format': 'CSV',
                    'name': 'hdx_test.csv',

                }
            ]
        }

        context = {'model': model, 'session': model.Session, 'user': user}
        package_dict = _get_action('package_create')(context, package)
        return package_dict


@pytest.mark.usefixtures("with_request_context")
class TestYtpRequestCreate(TestYtpRequestBase):

    @mock.patch('ckanext.ytp.request.logic.hdx_mailer')
    def test_member_request_create(self, mail_recipient):
        context = self._create_context()
        admin_context = self._create_context()
        self._create_user("tester")
        context['user'] = "tester"

        # self.assert_raises(NotFound, _get_action("member_request_create"), context,
        #                    {"group": "test_organization", 'role': "editor"})
        try:
            _get_action("member_request_create")(context, {"group": "test_organization", 'role': "editor"})
        except NotFound:
            assert True
        _get_action("organization_create")(admin_context, {
            "name": "test_organization",
            "description": "Test Description",
            'hdx_org_type': 'united_nations',
            "org_url": "https://test.test/test",
        })
        mrl = _get_action("member_request_list")(admin_context, {"group": "test_organization"})
        assert len(mrl) == 0
        # self.assert_len(_get_action("member_request_list")(admin_context, {"group": "test_organization"}), 0)

        _get_action("member_request_create")(context, {"group": "test_organization", 'role': "editor"})
        mrl = _get_action("member_request_list")(admin_context, {"group": "test_organization"})
        assert len(mrl) == 1
        # self.assert_len(_get_action("member_request_list")(admin_context, {"group": "test_organization"}), 1)


@pytest.mark.usefixtures("with_request_context")
class TestYtpRequestProcess(TestYtpRequestBase):

    @mock.patch('ckanext.ytp.request.logic.hdx_mailer')
    def test_member_request_process(self, mail_recipient):
        context = self._create_context()
        admin_context = self._create_context()
        self._create_user("tester1")
        context['user'] = "tester1"

        for organization, approve, result in [('test_process_approve', True, "active"), ('test_process_reject1', True, "active")]:
            try:
                admin_context = self._create_context()
                _get_action("organization_create")(admin_context, {
                    "name": organization,
                    "description": "Test Description",
                    'hdx_org_type': 'united_nations',
                    "org_url": "https://test.test/test",
                })
            except Exception as ex:
                assert False, 'There shouldn\'t be any exception'

            member = _get_action("member_request_create")(context, {"group": organization, 'role': "editor"})
            show_member = _get_action("member_request_show")(context, {"member": member['id']})
            assert show_member['state'] == "pending"

            _get_action("member_request_process")(admin_context, {"member": member['id'], "approve": approve})
            show_member = _get_action("member_request_show")(context, {"member": member['id']})
            assert show_member['state'] == result


@pytest.mark.usefixtures("with_request_context")
class TestYtpRequestOrgAdmins(TestYtpRequestBase):

    @mock.patch('ckanext.ytp.request.logic.hdx_mailer')
    def test_get_organization_admins(self, mail_recipient):
        context_user = self._create_context()
        user = self._create_user("test_admins_1")
        context_user['user'] = "test_admins_1"

        context_user_2 = self._create_context()
        user_2 = self._create_user("test_admins_2")
        context_user_2['user'] = "test_admins_2"

        context_admin = self._create_context()

        organization = _get_action("organization_create")(context_admin, {
            "name": 'test_admins',
            "description": "Test Description",
            'hdx_org_type': 'united_nations',
            "org_url": "https://test.test/test",
        })

        for admin in get_organization_admins(organization['id']):
            assert admin.id != user.id

        member = _get_action("member_request_create")(context_user, {"group": organization['id'], 'role': "editor"})
        _get_action("member_request_process")(context_admin, {"member": member['id'], "approve": False})

        for admin in get_organization_admins(organization['id']):
            assert admin.id != user.id

        member = _get_action("member_request_create")(context_user, {"group": organization['id'], 'role': "editor"})
        _get_action("member_request_process")(context_admin, {"member": member['id'], "approve": True})

        for admin in get_organization_admins(organization['id']):
            assert admin.id != user.id

        member = _get_action("member_request_create")(context_user_2, {"group": organization['id'], 'role': "admin"})
        _get_action("member_request_process")(context_admin, {"member": member['id'], "approve": True})

        ok = False
        for admin in get_organization_admins(organization['id']):
            if admin.id == user_2.id:
                ok = True

        if not ok:
            assert False, "User not found from organization admins"
