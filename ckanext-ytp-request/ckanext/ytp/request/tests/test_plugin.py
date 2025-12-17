import pytest
from unittest.mock import Mock, patch, MagicMock
from ckan.tests import factories
from ckanext.ytp.request.plugin import YtpRequestPlugin


class TestYtpRequestPlugin:
    """Tests for YtpRequestPlugin"""

    @pytest.fixture
    def plugin(self):
        """Create plugin instance"""
        return YtpRequestPlugin()

    def test_get_blueprint(self, plugin):
        """Test get_blueprint returns ytp_request blueprint"""
        with patch('ckanext.ytp.request.plugin.ytp_request') as mock_blueprint:
            result = plugin.get_blueprint()
            assert result == mock_blueprint

    def test_configure(self, plugin):
        """Test configure calls setup"""
        with patch('ckanext.ytp.request.plugin.setup') as mock_setup:
            plugin.configure({})
            mock_setup.assert_called_once()

    def test_get_function_dictionary(self, plugin):
        """Test _get_function_dictionary returns correct functions"""
        mock_module = Mock()
        mock_module.member_request_create = Mock()
        mock_module.member_request_list = Mock()
        mock_module.other_function = Mock()

        result = plugin._get_function_dictionary(mock_module, 'member_request_')

        assert 'member_request_create' in result
        assert 'member_request_list' in result
        assert 'other_function' not in result
        assert len(result) == 2

    def test_get_actions(self, plugin):
        """Test get_actions returns logic functions"""
        with patch('ckanext.ytp.request.plugin.logic') as mock_logic:
            mock_logic.member_request_create = Mock()
            mock_logic.member_request_list = Mock()
            mock_logic.other_function = Mock()

            with patch.object(plugin, '_get_function_dictionary') as mock_get_dict:
                expected_dict = {'member_request_create': Mock()}
                mock_get_dict.return_value = expected_dict
                result = plugin.get_actions()

                mock_get_dict.assert_called_once_with(mock_logic, 'member_request_')
                assert result == expected_dict

    def test_get_auth_functions(self, plugin):
        """Test get_auth_functions returns auth functions"""
        with patch('ckanext.ytp.request.plugin.auth') as mock_auth:
            mock_auth.member_request_process = Mock()
            mock_auth.member_request_cancel = Mock()
            mock_auth.other_function = Mock()

            with patch.object(plugin, '_get_function_dictionary') as mock_get_dict:
                expected_dict = {'member_request_process': Mock()}
                mock_get_dict.return_value = expected_dict
                result = plugin.get_auth_functions()

                mock_get_dict.assert_called_once_with(mock_auth, 'member_request_')
                assert result == expected_dict

    def test_list_organizations(self, plugin):
        """Test _list_organizations calls organization_list action"""
        user = factories.User()

        mock_c = Mock()
        mock_c.user = user['name']

        expected_orgs = [
            {'id': 'org1', 'name': 'Organization 1'},
            {'id': 'org2', 'name': 'Organization 2'}
        ]

        with (
            patch.object(plugin.__class__, 'c', mock_c, create=True),
            patch('ckanext.ytp.request.plugin.c', mock_c),
            patch('ckanext.ytp.request.plugin.toolkit.get_action') as mock_get_action
        ):
            mock_action = Mock(return_value=expected_orgs)
            mock_get_action.return_value = mock_action

            result = plugin._list_organizations()

            mock_get_action.assert_called_once_with('organization_list')
            mock_action.assert_called_once_with(
                {'user': user['name']},
                {
                    'all_fields': True,
                    'groups': [],
                    'type': 'organization'
                }
            )
            assert result == expected_orgs

    def test_request_title_and_link_no_user(self, plugin):
        """Test _request_title_and_link with no user"""
        mock_c = Mock()
        mock_c.user = None
        mock_c.userobj = None

        with (
            patch.object(plugin.__class__, 'c', mock_c, create=True),
            patch('ckanext.ytp.request.plugin.c', mock_c)
        ):
            title, link = plugin._request_title_and_link('org-id', 'org-name')

            assert title is None
            assert link is None

    def test_request_title_and_link_sysadmin(self, plugin):
        """Test _request_title_and_link for sysadmin"""
        user = factories.User(sysadmin=True)

        mock_c = Mock()
        mock_c.user = user['name']
        mock_c.userobj = Mock(sysadmin=True)

        with (
            patch.object(plugin.__class__, 'c', mock_c, create=True),
            patch('ckanext.ytp.request.plugin.c', mock_c),
            patch('ckanext.ytp.request.plugin._') as mock_translate
        ):
            mock_translate.return_value = 'admin'

            title, link = plugin._request_title_and_link('org-id', 'org-name')

            mock_translate.assert_called_once_with('admin')
            assert title == 'admin'
            assert link is None

    def test_request_title_and_link_no_member(self, plugin):
        """Test _request_title_and_link when user has no membership"""
        user = factories.User()

        mock_c = Mock()
        mock_c.user = user['name']
        mock_c.userobj = Mock(id=user['id'], sysadmin=False)

        with (
            patch.object(plugin.__class__, 'c', mock_c, create=True),
            patch('ckanext.ytp.request.plugin.c', mock_c),
            patch('ckanext.ytp.request.plugin.get_user_member') as mock_get_member,
            patch('ckanext.ytp.request.plugin._') as mock_translate,
            patch('ckanext.ytp.request.plugin.helpers.url_for') as mock_url_for
        ):
            mock_get_member.return_value = None
            mock_translate.return_value = 'Request membership'
            mock_url_for.return_value = '/member-request/new'

            title, link = plugin._request_title_and_link('org-id', 'org-name')

            mock_get_member.assert_called_once_with('org-id')
            mock_translate.assert_called_once_with('Request membership')
            mock_url_for.assert_called_once_with('ytp_request.new', selected_organization='org-name')
            assert title == 'Request membership'
            assert link == '/member-request/new'

    def test_request_title_and_link_pending_member(self, plugin):
        """Test _request_title_and_link for pending member"""
        user = factories.User()

        mock_member = Mock()
        mock_member.id = 'member-123'
        mock_member.state = 'pending'

        mock_c = Mock()
        mock_c.user = user['name']
        mock_c.userobj = Mock(id=user['id'], sysadmin=False)

        with (
            patch.object(plugin.__class__, 'c', mock_c, create=True),
            patch('ckanext.ytp.request.plugin.c', mock_c),
            patch('ckanext.ytp.request.plugin.get_user_member') as mock_get_member,
            patch('ckanext.ytp.request.plugin._') as mock_translate,
            patch('ckanext.ytp.request.plugin.helpers.url_for') as mock_url_for
        ):
            mock_get_member.return_value = mock_member
            mock_translate.return_value = 'Pending for approval'
            mock_url_for.return_value = '/member-request/show/member-123'

            title, link = plugin._request_title_and_link('org-id', 'org-name')

            mock_get_member.assert_called_once_with('org-id')
            mock_translate.assert_called_once_with('Pending for approval')
            mock_url_for.assert_called_once_with('member_request_show', member_id='member-123')
            assert title == 'Pending for approval'
            assert link == '/member-request/show/member-123'

    def test_request_title_and_link_active_member(self, plugin):
        """Test _request_title_and_link for active member"""
        user = factories.User()

        mock_member = Mock()
        mock_member.id = 'member-123'
        mock_member.state = 'active'
        mock_member.capacity = 'editor'

        mock_c = Mock()
        mock_c.user = user['name']
        mock_c.userobj = Mock(id=user['id'], sysadmin=False)

        with (
            patch.object(plugin.__class__, 'c', mock_c, create=True),
            patch('ckanext.ytp.request.plugin.c', mock_c),
            patch('ckanext.ytp.request.plugin.get_user_member') as mock_get_member,
            patch('ckanext.ytp.request.plugin._') as mock_translate
        ):
            mock_get_member.return_value = mock_member
            mock_translate.return_value = 'editor'

            title, link = plugin._request_title_and_link('org-id', 'org-name')

            mock_get_member.assert_called_once_with('org-id')
            mock_translate.assert_called_once_with('editor')
            assert title == 'editor'
            assert link is None

    def test_get_helpers(self, plugin):
        """Test get_helpers returns helper functions"""
        helpers = plugin.get_helpers()

        assert 'list_organizations' in helpers
        assert 'request_title_and_link' in helpers
        assert callable(helpers['list_organizations'])
        assert callable(helpers['request_title_and_link'])
        assert helpers['list_organizations'] == plugin._list_organizations
        assert helpers['request_title_and_link'] == plugin._request_title_and_link
