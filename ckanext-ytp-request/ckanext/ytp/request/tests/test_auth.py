import pytest
from unittest.mock import Mock, patch, MagicMock
from ckan import model
from ckan.tests import factories
from ckanext.ytp.request import auth as auth_module
from ckanext.ytp.request.auth import member_request_create, member_request_cancel, member_request_process


class TestMemberRequestMembershipCancel:
    """Tests for member_request_membership_cancel"""

    def test_membership_cancel_no_user(self):
        """Test with no user logged in"""
        mock_c = Mock()
        mock_c.userobj = None

        with patch.object(auth_module, 'c', mock_c):
            context = {'user': None, 'model': model}
            data_dict = {'organization_id': 'test-org'}

            result = auth_module.member_request_membership_cancel(context, data_dict)

            assert result['success'] is False

    def test_membership_cancel_no_active_member(self):
        """Test when user has no active membership"""
        user = factories.User()

        mock_c = Mock()
        mock_c.userobj = Mock(id=user['id'])

        with (
            patch.object(auth_module, 'c', mock_c),
            patch.object(auth_module, 'get_user_member') as mock_get_member,
        ):
            mock_get_member.return_value = None

            context = {'user': user['name'], 'model': model}
            data_dict = {'organization_id': 'test-org'}

            result = auth_module.member_request_membership_cancel(context, data_dict)

            assert result['success'] is False
            mock_get_member.assert_called_once_with('test-org', 'active')

    def test_membership_cancel_wrong_table_name(self):
        """Test when member has wrong table_name"""
        user = factories.User()

        mock_member = Mock()
        mock_member.table_name = 'package'
        mock_member.table_id = user['id']
        mock_member.state = 'active'

        mock_c = Mock()
        mock_c.userobj = Mock(id=user['id'])

        with (
            patch.object(auth_module, 'c', mock_c),
            patch.object(auth_module, 'get_user_member') as mock_get_member,
        ):
            mock_get_member.return_value = mock_member

            context = {'user': user['name'], 'model': model}
            data_dict = {'organization_id': 'test-org'}

            result = auth_module.member_request_membership_cancel(context, data_dict)

            assert result['success'] is False

    def test_membership_cancel_wrong_user(self):
        """Test when member belongs to different user"""
        user = factories.User()
        other_user = factories.User()

        mock_member = Mock()
        mock_member.table_name = 'user'
        mock_member.table_id = other_user['id']
        mock_member.state = 'active'

        mock_c = Mock()
        mock_c.userobj = Mock(id=user['id'])

        with (
            patch.object(auth_module, 'c', mock_c),
            patch.object(auth_module, 'get_user_member') as mock_get_member,
        ):
            mock_get_member.return_value = mock_member

            context = {'user': user['name'], 'model': model}
            data_dict = {'organization_id': 'test-org'}

            result = auth_module.member_request_membership_cancel(context, data_dict)

            assert result['success'] is False

    def test_membership_cancel_wrong_state(self):
        """Test when member is not in active state"""
        user = factories.User()

        mock_member = Mock()
        mock_member.table_name = 'user'
        mock_member.table_id = user['id']
        mock_member.state = 'pending'

        mock_c = Mock()
        mock_c.userobj = Mock(id=user['id'])

        with (
            patch.object(auth_module, 'c', mock_c),
            patch.object(auth_module, 'get_user_member') as mock_get_member,
        ):
            mock_get_member.return_value = mock_member

            context = {'user': user['name'], 'model': model}
            data_dict = {'organization_id': 'test-org'}

            result = auth_module.member_request_membership_cancel(context, data_dict)

            assert result['success'] is False

    def test_membership_cancel_success(self):
        """Test successful membership cancellation"""
        user = factories.User()

        mock_member = Mock()
        mock_member.table_name = 'user'
        mock_member.table_id = user['id']
        mock_member.state = 'active'

        mock_c = Mock()
        mock_c.userobj = Mock(id=user['id'])

        with (
            patch.object(auth_module, 'c', mock_c),
            patch.object(auth_module, 'get_user_member') as mock_get_member,
        ):
            mock_get_member.return_value = mock_member

            context = {'user': user['name'], 'model': model}
            data_dict = {'organization_id': 'test-org'}

            result = auth_module.member_request_membership_cancel(context, data_dict)

            assert result['success'] is True


class TestMemberRequestCreate:
    """Tests for member_request_create authorization function"""

    def test_anonymous_user_denied(self):
        """Test that anonymous users are denied access"""
        context = {'user': None}
        data_dict = {'organization_id': 'test-org'}

        with patch('ckanext.ytp.request.auth.authz.auth_is_anon_user', return_value=True):
            result = member_request_create(context, data_dict)

        assert result['success'] is False
        assert 'not logged in' in result['msg'].lower()

    def test_authenticated_user_no_organization(self):
        """Test authenticated user without organization_id"""
        context = {'user': 'test_user'}
        data_dict = {}

        with patch('ckanext.ytp.request.auth.authz.auth_is_anon_user', return_value=False):
            result = member_request_create(context, data_dict)

        assert result['success'] is True

    def test_authenticated_user_with_organization_no_existing_member(self):
        """Test authenticated user with organization and no existing membership"""
        context = {'user': 'test_user'}
        data_dict = {'organization_id': 'test-org'}

        with (
            patch('ckanext.ytp.request.auth.authz.auth_is_anon_user', return_value=False),
            patch('ckanext.ytp.request.auth.get_user_member', return_value=None),
        ):
            result = member_request_create(context, data_dict)

        assert result['success'] is True

    def test_authenticated_user_with_existing_membership(self):
        """Test authenticated user with existing membership or pending request"""
        context = {'user': 'test_user'}
        data_dict = {'organization_id': 'test-org'}

        mock_member = Mock()

        with (
            patch('ckanext.ytp.request.auth.authz.auth_is_anon_user', return_value=False),
            patch('ckanext.ytp.request.auth.get_user_member', return_value=mock_member),
        ):
            result = member_request_create(context, data_dict)

        assert result['success'] is False
        assert 'pending request' in result['msg'].lower() or 'active membership' in result['msg'].lower()

    def test_none_data_dict(self):
        """Test with None data_dict"""
        context = {'user': 'test_user'}
        data_dict = None

        with patch('ckanext.ytp.request.auth.authz.auth_is_anon_user', return_value=False):
            result = member_request_create(context, data_dict)

        assert result['success'] is True


class TestMemberRequestCancel:
    """Tests for member_request_cancel authorization function"""

    @pytest.fixture
    def mock_context(self):
        """Create a mock context with userobj"""
        context = MagicMock()
        context.userobj = Mock()
        context.userobj.id = 'test-user-id'
        return context

    def test_cancel_no_userobj(self):
        """Test with no user logged in"""
        mock_c = Mock()
        mock_c.userobj = None

        with patch.object(auth_module, 'c', mock_c):
            context = {}
            data_dict = {'organization_id': 'test-org'}

            result = member_request_cancel(context, data_dict)

            assert result['success'] is False

    def test_cancel_with_member_id_success(self):
        """Test canceling with valid member ID"""
        mock_c = Mock()
        mock_c.userobj = Mock(id='test-user-id')

        mock_member = Mock()
        mock_member.table_name = 'user'
        mock_member.table_id = 'test-user-id'
        mock_member.state = 'pending'

        with (
            patch.object(auth_module, 'c', mock_c),
            patch.object(auth_module.model.Member, 'get', return_value=mock_member) as mock_get,
        ):
            context = {}
            data_dict = {'member': 'member-id-123'}

            result = member_request_cancel(context, data_dict)

            assert result['success'] is True
            mock_get.assert_called_once_with('member-id-123')

    def test_cancel_with_organization_id_success(self):
        """Test canceling with organization ID"""
        mock_c = Mock()
        mock_c.userobj = Mock(id='test-user-id')

        mock_member = Mock()
        mock_member.table_name = 'user'
        mock_member.table_id = 'test-user-id'
        mock_member.state = 'pending'

        with (
            patch.object(auth_module, 'c', mock_c),
            patch.object(auth_module, 'get_user_member', return_value=mock_member) as mock_get,
        ):
            context = {}
            data_dict = {'organization_id': 'test-org'}

            result = member_request_cancel(context, data_dict)

            assert result['success'] is True
            mock_get.assert_called_once_with('test-org', 'pending')

    def test_cancel_member_not_found(self):
        """Test when member is not found"""
        mock_c = Mock()
        mock_c.userobj = Mock(id='test-user-id')

        with (
            patch.object(auth_module, 'c', mock_c),
            patch.object(auth_module.model.Member, 'get', return_value=None),
        ):
            context = {}
            data_dict = {'member': 'member-id-123'}

            result = member_request_cancel(context, data_dict)

            assert result['success'] is False

    def test_cancel_wrong_user(self):
        """Test when member belongs to different user"""
        mock_c = Mock()
        mock_c.userobj = Mock(id='test-user-id')

        mock_member = Mock()
        mock_member.table_name = 'user'
        mock_member.table_id = 'different-user-id'
        mock_member.state = 'pending'

        with (
            patch.object(auth_module, 'c', mock_c),
            patch.object(auth_module.model.Member, 'get', return_value=mock_member),
        ):
            context = {}
            data_dict = {'member': 'member-id-123'}

            result = member_request_cancel(context, data_dict)

            assert result['success'] is False

    def test_cancel_wrong_state(self):
        """Test when member is not in pending state"""
        mock_c = Mock()
        mock_c.userobj = Mock(id='test-user-id')

        mock_member = Mock()
        mock_member.table_name = 'user'
        mock_member.table_id = 'test-user-id'
        mock_member.state = 'active'

        with (
            patch.object(auth_module, 'c', mock_c),
            patch.object(auth_module.model.Member, 'get', return_value=mock_member),
        ):
            context = {}
            data_dict = {'member': 'member-id-123'}

            result = member_request_cancel(context, data_dict)

            assert result['success'] is False

    def test_cancel_wrong_table_name(self):
        """Test when member table_name is not 'user'"""
        mock_c = Mock()
        mock_c.userobj = Mock(id='test-user-id')

        mock_member = Mock()
        mock_member.table_name = 'group'
        mock_member.table_id = 'test-user-id'
        mock_member.state = 'pending'

        with (
            patch.object(auth_module, 'c', mock_c),
            patch.object(auth_module.model.Member, 'get', return_value=mock_member),
        ):
            context = {}
            data_dict = {'member': 'member-id-123'}

            result = member_request_cancel(context, data_dict)

            assert result['success'] is False


class TestMemberRequestProcess:
    """Tests for member_request_process authorization function"""

    def test_process_sysadmin_success(self):
        """Test that sysadmin can process any request"""
        with patch.object(auth_module.authz, 'is_sysadmin', return_value=True):
            context = {'user': 'sysadmin-user'}
            data_dict = {'member': 'member-id-123'}

            result = member_request_process(context, data_dict)

            assert result['success'] is True

    def test_process_user_not_found(self):
        """Test when user is not found"""
        with (
            patch.object(auth_module.authz, 'is_sysadmin', return_value=False),
            patch.object(auth_module.model.User, 'get', return_value=None),
        ):
            context = {'user': 'unknown-user'}
            data_dict = {'member': 'member-id-123'}

            result = member_request_process(context, data_dict)

            assert result['success'] is False

    def test_process_member_not_found(self):
        """Test when member is not found"""
        mock_user = Mock()

        with (
            patch.object(auth_module.authz, 'is_sysadmin', return_value=False),
            patch.object(auth_module.model.User, 'get', return_value=mock_user),
            patch.object(auth_module.model.Member, 'get', return_value=None),
        ):
            context = {'user': 'test-user'}
            data_dict = {'member': 'member-id-123'}

            result = member_request_process(context, data_dict)

            assert result['success'] is False

    def test_process_member_not_user_type(self):
        """Test when member table_name is not 'user'"""
        mock_user = Mock()
        mock_member = Mock()
        mock_member.table_name = 'group'

        with (
            patch.object(auth_module.authz, 'is_sysadmin', return_value=False),
            patch.object(auth_module.model.User, 'get', return_value=mock_user),
            patch.object(auth_module.model.Member, 'get', return_value=mock_member),
        ):
            context = {'user': 'test-user'}
            data_dict = {'member': 'member-id-123'}

            result = member_request_process(context, data_dict)

            assert result['success'] is False

    def test_process_user_is_admin_success(self):
        """Test when user is admin of the organization"""
        mock_user = Mock()
        mock_user.id = 'test-user-id'

        mock_member = Mock()
        mock_member.table_name = 'user'
        mock_member.group_id = 'test-org-id'

        mock_query = Mock()
        mock_query.count = Mock(return_value=1)

        with (
            patch.object(auth_module.authz, 'is_sysadmin', return_value=False),
            patch.object(auth_module.model.User, 'get', return_value=mock_user),
            patch.object(auth_module.model.Member, 'get', return_value=mock_member),
            patch.object(auth_module.model, 'Session') as mock_session,
        ):
            mock_session.query.return_value.filter.return_value.filter.return_value.filter.return_value.filter.return_value.filter.return_value = mock_query

            context = {'user': 'test-user'}
            data_dict = {'member': 'member-id-123'}

            result = member_request_process(context, data_dict)

            assert result['success'] is True

    def test_process_user_not_admin_failure(self):
        """Test when user is not admin of the organization"""
        mock_user = Mock()
        mock_user.id = 'test-user-id'

        mock_member = Mock()
        mock_member.table_name = 'user'
        mock_member.group_id = 'test-org-id'

        mock_query = Mock()
        mock_query.count = Mock(return_value=0)

        with (
            patch.object(auth_module.authz, 'is_sysadmin', return_value=False),
            patch.object(auth_module.model.User, 'get', return_value=mock_user),
            patch.object(auth_module.model.Member, 'get', return_value=mock_member),
            patch.object(auth_module.model, 'Session') as mock_session,
        ):
            mock_session.query.return_value.filter.return_value.filter.return_value.filter.return_value.filter.return_value.filter.return_value = mock_query

            context = {'user': 'test-user'}
            data_dict = {'member': 'member-id-123'}

            result = member_request_process(context, data_dict)

            assert result['success'] is False
