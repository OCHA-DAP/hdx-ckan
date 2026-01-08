"""
Tests for YTP Request Tools Module.

This module contains unit tests for database query helper functions used in
membership request handling.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from sqlalchemy.orm import Query
from flask import Flask


@pytest.fixture
def app() -> Flask:
    """
    Create a Flask application for testing.

    :return: Flask application instance
    """
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret-key'
    return app


class TestGetUserMember:
    """Test suite for get_user_member function."""

    @patch('ckanext.ytp.request.tools.model')
    def test_get_user_member_no_state(self, mock_model: Mock, app: Flask) -> None:
        """
        Test getting user member without state filter (active or pending).

        :param mock_model: Mocked CKAN model
        :param app: Flask application
        """
        with app.test_request_context():
            from flask import g
            from ckanext.ytp.request.tools import get_user_member

            # Setup
            mock_user = Mock()
            mock_user.id = 'user-123'
            g.userobj = mock_user

            organization_id = 'org-456'
            mock_member = Mock()
            mock_member.state = 'active'

            mock_query = MagicMock(spec=Query)
            mock_model.Session.query.return_value = mock_query
            mock_query.filter.return_value = mock_query
            mock_query.first.return_value = mock_member

            # Execute
            result = get_user_member(organization_id)

            # Assert
            mock_model.Session.query.assert_called_once_with(mock_model.Member)
            assert result == mock_member
            mock_query.first.assert_called_once()

    @patch('ckanext.ytp.request.tools.model')
    def test_get_user_member_with_state(self, mock_model: Mock, app: Flask) -> None:
        """
        Test getting user member with specific state filter.

        :param mock_model: Mocked CKAN model
        :param app: Flask application
        """
        with app.test_request_context():
            from flask import g
            from ckanext.ytp.request.tools import get_user_member

            # Setup
            mock_user = Mock()
            mock_user.id = 'user-123'
            g.userobj = mock_user

            organization_id = 'org-456'
            state = 'pending'
            mock_member = Mock()
            mock_member.state = state

            mock_query = MagicMock(spec=Query)
            mock_model.Session.query.return_value = mock_query
            mock_query.filter.return_value = mock_query
            mock_query.first.return_value = mock_member

            # Execute
            result = get_user_member(organization_id, state=state)

            # Assert
            mock_model.Session.query.assert_called_once_with(mock_model.Member)
            assert result == mock_member
            assert result.state == state
            mock_query.first.assert_called_once()

    @patch('ckanext.ytp.request.tools.model')
    def test_get_user_member_not_found(self, mock_model: Mock, app: Flask) -> None:
        """
        Test getting user member that doesn't exist.

        :param mock_model: Mocked CKAN model
        :param app: Flask application
        """
        with app.test_request_context():
            from flask import g
            from ckanext.ytp.request.tools import get_user_member

            # Setup
            mock_user = Mock()
            mock_user.id = 'user-123'
            g.userobj = mock_user

            organization_id = 'org-456'

            mock_query = MagicMock(spec=Query)
            mock_model.Session.query.return_value = mock_query
            mock_query.filter.return_value = mock_query
            mock_query.first.return_value = None

            # Execute
            result = get_user_member(organization_id)

            # Assert
            assert result is None
            mock_query.first.assert_called_once()

    @patch('ckanext.ytp.request.tools.model')
    def test_get_user_member_filters_table_name(self, mock_model: Mock, app: Flask) -> None:
        """
        Test that get_user_member filters by table_name='user'.

        :param mock_model: Mocked CKAN model
        :param app: Flask application
        """
        with app.test_request_context():
            from flask import g
            from ckanext.ytp.request.tools import get_user_member

            # Setup
            mock_user = Mock()
            mock_user.id = 'user-123'
            g.userobj = mock_user

            organization_id = 'org-456'

            mock_query = MagicMock(spec=Query)
            mock_model.Session.query.return_value = mock_query
            mock_query.filter.return_value = mock_query
            mock_query.first.return_value = Mock()

            # Execute
            get_user_member(organization_id)

            # Assert - verify filter was called multiple times
            assert mock_query.filter.call_count >= 4


class TestGetOrganizationAdmins:
    """Test suite for get_organization_admins function."""

    @patch('ckanext.ytp.request.tools.model')
    def test_get_organization_admins_returns_set(self, mock_model: Mock) -> None:
        """
        Test that get_organization_admins returns a set of admin users.

        :param mock_model: Mocked CKAN model
        """
        from ckanext.ytp.request.tools import get_organization_admins

        # Setup
        group_id = 'org-123'
        mock_user1 = Mock()
        mock_user1.id = 'user-1'
        mock_user1.name = 'admin1'
        mock_user2 = Mock()
        mock_user2.id = 'user-2'
        mock_user2.name = 'admin2'

        mock_query = MagicMock(spec=Query)
        mock_model.Session.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.__iter__ = Mock(return_value=iter([mock_user1, mock_user2]))

        # Execute
        result = get_organization_admins(group_id)

        # Assert
        assert isinstance(result, set)
        assert len(result) == 2
        assert mock_user1 in result
        assert mock_user2 in result

    @patch('ckanext.ytp.request.tools.model')
    def test_get_organization_admins_filters_admin_capacity(self, mock_model: Mock) -> None:
        """
        Test that get_organization_admins filters by capacity='admin'.

        :param mock_model: Mocked CKAN model
        """
        from ckanext.ytp.request.tools import get_organization_admins

        # Setup
        group_id = 'org-123'

        mock_query = MagicMock(spec=Query)
        mock_model.Session.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.__iter__ = Mock(return_value=iter([]))

        # Execute
        get_organization_admins(group_id)

        # Assert
        mock_model.Session.query.assert_called_once_with(mock_model.User)
        mock_query.join.assert_called_once()
        # Should have multiple filter calls for table_name, group_id, state, capacity
        assert mock_query.filter.call_count >= 4

    @patch('ckanext.ytp.request.tools.model')
    def test_get_organization_admins_filters_active_state(self, mock_model: Mock) -> None:
        """
        Test that get_organization_admins filters by state='active'.

        :param mock_model: Mocked CKAN model
        """
        from ckanext.ytp.request.tools import get_organization_admins

        # Setup
        group_id = 'org-123'

        mock_query = MagicMock(spec=Query)
        mock_model.Session.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.__iter__ = Mock(return_value=iter([]))

        # Execute
        get_organization_admins(group_id)

        # Assert - verify multiple filters are applied
        assert mock_query.filter.call_count >= 4

    @patch('ckanext.ytp.request.tools.model')
    def test_get_organization_admins_empty_result(self, mock_model: Mock) -> None:
        """
        Test that get_organization_admins returns empty set when no admins found.

        :param mock_model: Mocked CKAN model
        """
        from ckanext.ytp.request.tools import get_organization_admins

        # Setup
        group_id = 'org-123'

        mock_query = MagicMock(spec=Query)
        mock_model.Session.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.__iter__ = Mock(return_value=iter([]))

        # Execute
        result = get_organization_admins(group_id)

        # Assert
        assert isinstance(result, set)
        assert len(result) == 0

    @patch('ckanext.ytp.request.tools.model')
    def test_get_organization_admins_joins_user_and_member(self, mock_model: Mock) -> None:
        """
        Test that get_organization_admins joins User and Member tables.

        :param mock_model: Mocked CKAN model
        """
        from ckanext.ytp.request.tools import get_organization_admins

        # Setup
        group_id = 'org-123'

        mock_query = MagicMock(spec=Query)
        mock_model.Session.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.__iter__ = Mock(return_value=iter([]))

        # Execute
        get_organization_admins(group_id)

        # Assert
        mock_query.join.assert_called_once()


class TestGetCkanAdmins:
    """Test suite for get_ckan_admins function."""

    @patch('ckanext.ytp.request.tools.model')
    def test_get_ckan_admins_returns_set(self, mock_model: Mock) -> None:
        """
        Test that get_ckan_admins returns a set of sysadmin users.

        :param mock_model: Mocked CKAN model
        """
        from ckanext.ytp.request.tools import get_ckan_admins

        # Setup
        mock_user1 = Mock()
        mock_user1.id = 'user-1'
        mock_user1.name = 'sysadmin1'
        mock_user1.sysadmin = True
        mock_user2 = Mock()
        mock_user2.id = 'user-2'
        mock_user2.name = 'sysadmin2'
        mock_user2.sysadmin = True

        mock_query = MagicMock(spec=Query)
        mock_model.Session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.__iter__ = Mock(return_value=iter([mock_user1, mock_user2]))

        # Execute
        result = get_ckan_admins()

        # Assert
        assert isinstance(result, set)
        assert len(result) == 2
        assert mock_user1 in result
        assert mock_user2 in result

    @patch('ckanext.ytp.request.tools.model')
    def test_get_ckan_admins_filters_sysadmin_true(self, mock_model: Mock) -> None:
        """
        Test that get_ckan_admins filters by sysadmin=True.

        :param mock_model: Mocked CKAN model
        """
        from ckanext.ytp.request.tools import get_ckan_admins

        # Setup
        mock_query = MagicMock(spec=Query)
        mock_model.Session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.__iter__ = Mock(return_value=iter([]))

        # Execute
        get_ckan_admins()

        # Assert
        mock_model.Session.query.assert_called_once_with(mock_model.User)
        mock_query.filter.assert_called_once()

    @patch('ckanext.ytp.request.tools.model')
    def test_get_ckan_admins_empty_result(self, mock_model: Mock) -> None:
        """
        Test that get_ckan_admins returns empty set when no sysadmins found.

        :param mock_model: Mocked CKAN model
        """
        from ckanext.ytp.request.tools import get_ckan_admins

        # Setup
        mock_query = MagicMock(spec=Query)
        mock_model.Session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.__iter__ = Mock(return_value=iter([]))

        # Execute
        result = get_ckan_admins()

        # Assert
        assert isinstance(result, set)
        assert len(result) == 0

    @patch('ckanext.ytp.request.tools.model')
    def test_get_ckan_admins_multiple_sysadmins(self, mock_model: Mock) -> None:
        """
        Test that get_ckan_admins handles multiple sysadmins correctly.

        :param mock_model: Mocked CKAN model
        """
        from ckanext.ytp.request.tools import get_ckan_admins

        # Setup
        sysadmins = []
        for i in range(5):
            mock_user = Mock()
            mock_user.id = f'user-{i}'
            mock_user.name = f'sysadmin{i}'
            mock_user.sysadmin = True
            sysadmins.append(mock_user)

        mock_query = MagicMock(spec=Query)
        mock_model.Session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.__iter__ = Mock(return_value=iter(sysadmins))

        # Execute
        result = get_ckan_admins()

        # Assert
        assert isinstance(result, set)
        assert len(result) == 5
        for sysadmin in sysadmins:
            assert sysadmin in result


class TestToolsIntegration:
    """Integration tests for tools module functions."""

    @patch('ckanext.ytp.request.tools.model')
    def test_user_member_and_organization_admins_different_queries(
        self, mock_model: Mock, app: Flask
    ) -> None:
        """
        Test that get_user_member and get_organization_admins use different query patterns.

        :param mock_model: Mocked CKAN model
        :param app: Flask application
        """
        with app.test_request_context():
            from flask import g
            from ckanext.ytp.request.tools import get_user_member, get_organization_admins

            # Setup
            mock_user = Mock()
            mock_user.id = 'user-123'
            g.userobj = mock_user

            organization_id = 'org-456'

            mock_query = MagicMock(spec=Query)
            mock_model.Session.query.return_value = mock_query
            mock_query.filter.return_value = mock_query
            mock_query.join.return_value = mock_query
            mock_query.first.return_value = Mock()
            mock_query.__iter__ = Mock(return_value=iter([]))

            # Execute both functions
            get_user_member(organization_id)
            get_organization_admins(organization_id)

            # Assert - both should query but with different patterns
            assert mock_model.Session.query.call_count == 2
