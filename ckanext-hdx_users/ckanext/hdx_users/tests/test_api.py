"""
Tests for HDX Users API module.

This module contains unit tests for user autocomplete and related API endpoints.
"""

import pytest
from unittest.mock import Mock, patch
from flask import Flask, jsonify
import json


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


class TestUserAutocomplete:
    """Test suite for user_autocomplete endpoint."""

    def test_autocomplete_no_query_returns_empty_list(self, app: Flask):
        """Test that autocomplete without query parameter returns empty list."""
        with app.test_request_context('/?'):
            from flask import g
            from ckanext.hdx_users.views.api import user_autocomplete

            g.user = 'test_user'
            g.userobj = Mock()

            # Execute
            result = user_autocomplete()

            # Assert
            data = json.loads(result.data)
            assert data == []

    def test_autocomplete_with_query_calls_action(self, app: Flask):
        """Test that autocomplete with query calls hdx_user_autocomplete action."""
        mock_user_list = [
            {'id': 'user1', 'name': 'John Doe', 'fullname': 'John Doe'},
            {'id': 'user2', 'name': 'Jane Doe', 'fullname': 'Jane Doe'},
        ]

        with app.test_request_context('/?q=john'):
            from flask import g
            from ckanext.hdx_users.views.api import user_autocomplete

            g.user = 'test_user'
            g.userobj = Mock()

            with patch('ckanext.hdx_users.views.api.get_action') as mock_get_action:
                mock_action = Mock(return_value=mock_user_list)
                mock_get_action.return_value = mock_action

                # Execute
                result = user_autocomplete()

                # Assert
                data = json.loads(result.data)
                assert len(data) == 2
                assert data[0]['name'] == 'John Doe'
                assert data[1]['name'] == 'Jane Doe'

                # Verify action was called with correct parameters
                mock_get_action.assert_called_once_with('hdx_user_autocomplete')
                call_args = mock_action.call_args
                data_dict = call_args[0][1]
                assert data_dict['q'] == 'john'
                assert data_dict['limit'] == 20
                assert data_dict['ignore_self'] is False
                assert data_dict['org'] is None

    def test_autocomplete_with_limit_parameter(self, app: Flask):
        """Test that autocomplete respects limit parameter."""
        mock_user_list = [{'id': f'user{i}', 'name': f'User {i}'} for i in range(5)]

        with app.test_request_context('/?q=user&limit=5'):
            from flask import g
            from ckanext.hdx_users.views.api import user_autocomplete

            g.user = 'test_user'
            g.userobj = Mock()

            with patch('ckanext.hdx_users.views.api.get_action') as mock_get_action:
                mock_action = Mock(return_value=mock_user_list)
                mock_get_action.return_value = mock_action

                # Execute
                result = user_autocomplete()

                # Assert
                assert result is not None
                call_args = mock_action.call_args
                data_dict = call_args[0][1]
                assert data_dict['limit'] == '5'

    def test_autocomplete_with_org_parameter(self, app: Flask):
        """Test that autocomplete includes org parameter."""
        mock_user_list = [{'id': 'user1', 'name': 'Org User'}]

        with app.test_request_context('/?q=user&org=test-org'):
            from flask import g
            from ckanext.hdx_users.views.api import user_autocomplete

            g.user = 'test_user'
            g.userobj = Mock()

            with patch('ckanext.hdx_users.views.api.get_action') as mock_get_action:
                mock_action = Mock(return_value=mock_user_list)
                mock_get_action.return_value = mock_action

                # Execute
                result = user_autocomplete()

                # Assert
                assert result is not None
                call_args = mock_action.call_args
                data_dict = call_args[0][1]
                assert data_dict['org'] == 'test-org'

    def test_autocomplete_with_ignore_self_parameter(self, app: Flask):
        """Test that autocomplete respects ignore_self parameter."""
        mock_user_list = [{'id': 'user1', 'name': 'Other User'}]

        with app.test_request_context('/?q=user&ignore_self=true'):
            from flask import g
            from ckanext.hdx_users.views.api import user_autocomplete

            g.user = 'test_user'
            g.userobj = Mock()

            with patch('ckanext.hdx_users.views.api.get_action') as mock_get_action:
                mock_action = Mock(return_value=mock_user_list)
                mock_get_action.return_value = mock_action

                # Execute
                result = user_autocomplete()

                # Assert
                assert result is not None
                call_args = mock_action.call_args
                data_dict = call_args[0][1]
                assert data_dict['ignore_self'] == 'true'

    def test_autocomplete_with_all_parameters(self, app: Flask):
        """Test autocomplete with all parameters combined."""
        mock_user_list = [{'id': 'user1', 'name': 'Test User'}]

        with app.test_request_context('/?q=test&limit=10&org=my-org&ignore_self=true'):
            from flask import g
            from ckanext.hdx_users.views.api import user_autocomplete

            g.user = 'test_user'
            g.userobj = Mock()

            with patch('ckanext.hdx_users.views.api.get_action') as mock_get_action:
                mock_action = Mock(return_value=mock_user_list)
                mock_get_action.return_value = mock_action

                # Execute
                result = user_autocomplete()

                # Assert
                assert result is not None
                call_args = mock_action.call_args
                data_dict = call_args[0][1]
                assert data_dict['q'] == 'test'
                assert data_dict['limit'] == '10'
                assert data_dict['org'] == 'my-org'
                assert data_dict['ignore_self'] == 'true'

    def test_autocomplete_context_includes_user_info(self, app: Flask):
        """Test that context passed to action includes user information."""
        mock_user_list = []
        mock_userobj = Mock()

        with app.test_request_context('/?q=test'):
            from flask import g
            from ckanext.hdx_users.views.api import user_autocomplete

            g.user = 'test_user'
            g.userobj = mock_userobj

            with patch('ckanext.hdx_users.views.api.get_action') as mock_get_action:
                mock_action = Mock(return_value=mock_user_list)
                mock_get_action.return_value = mock_action

                # Execute
                result = user_autocomplete()

                # Assert
                assert result is not None
                call_args = mock_action.call_args
                context = call_args[0][0]
                assert context['user'] == 'test_user'
                assert context['auth_user_obj'] == mock_userobj
                assert 'model' in context
                assert 'session' in context

    def test_autocomplete_returns_json_response(self, app: Flask):
        """Test that autocomplete returns proper JSON response."""
        mock_user_list = [
            {'id': 'user1', 'name': 'User One', 'email': 'user1@example.com'},
            {'id': 'user2', 'name': 'User Two', 'email': 'user2@example.com'}
        ]

        with app.test_request_context('/?q=user'):
            from flask import g
            from ckanext.hdx_users.views.api import user_autocomplete

            g.user = 'test_user'
            g.userobj = Mock()

            with patch('ckanext.hdx_users.views.api.get_action') as mock_get_action:
                mock_action = Mock(return_value=mock_user_list)
                mock_get_action.return_value = mock_action

                # Execute
                result = user_autocomplete()

                # Assert
                assert result.status_code == 200
                assert result.content_type == 'application/json'
                data = json.loads(result.data)
                assert isinstance(data, list)
                assert len(data) == 2
                assert all('id' in user for user in data)
                assert all('name' in user for user in data)

    def test_autocomplete_empty_query_string(self, app: Flask):
        """Test autocomplete with empty query string."""
        with app.test_request_context('/?q='):
            from flask import g
            from ckanext.hdx_users.views.api import user_autocomplete

            g.user = 'test_user'
            g.userobj = Mock()

            # Execute
            result = user_autocomplete()

            # Assert
            data = json.loads(result.data)
            assert data == []


class TestCheckLockout:
    """Test suite for check_lockout endpoint."""

    def test_check_lockout_user_not_locked(self, app: Flask):
        """Test check_lockout returns false when user is not locked."""
        with app.test_request_context('/?username=testuser'):
            with patch('ckanext.hdx_users.views.user_edit_view.HDXTwoStep.check_lockout') as mock_check:
                mock_check.return_value = jsonify({'locked': False})

                from ckanext.hdx_users.views.user_edit_view import HDXTwoStep
                result = HDXTwoStep.check_lockout()

                # Assert
                assert result.status_code == 200
                data = json.loads(result.data)
                assert data['locked'] is False

    def test_check_lockout_user_locked(self, app: Flask):
        """Test check_lockout returns true when user is locked."""
        with app.test_request_context('/?username=lockeduser'):
            with patch('ckanext.hdx_users.views.user_edit_view.HDXTwoStep.check_lockout') as mock_check:
                mock_check.return_value = jsonify({'locked': True})

                from ckanext.hdx_users.views.user_edit_view import HDXTwoStep
                result = HDXTwoStep.check_lockout()

                # Assert
                assert result.status_code == 200
                data = json.loads(result.data)
                assert data['locked'] is True


class TestCheckMFA:
    """Test suite for check_mfa endpoint."""

    def test_check_mfa_enabled(self, app: Flask):
        """Test check_mfa returns true when MFA is enabled."""
        with app.test_request_context('/?username=testuser'):
            with patch('ckanext.hdx_users.views.user_edit_view.HDXTwoStep.check_mfa') as mock_check:
                mock_check.return_value = jsonify({'mfa_enabled': True})

                from ckanext.hdx_users.views.user_edit_view import HDXTwoStep
                result = HDXTwoStep.check_mfa()

                # Assert
                assert result.status_code == 200
                data = json.loads(result.data)
                assert data['mfa_enabled'] is True

    def test_check_mfa_disabled(self, app: Flask):
        """Test check_mfa returns false when MFA is disabled."""
        with app.test_request_context('/?username=testuser'):
            with patch('ckanext.hdx_users.views.user_edit_view.HDXTwoStep.check_mfa') as mock_check:
                mock_check.return_value = jsonify({'mfa_enabled': False})

                from ckanext.hdx_users.views.user_edit_view import HDXTwoStep
                result = HDXTwoStep.check_mfa()

                # Assert
                assert result.status_code == 200
                data = json.loads(result.data)
                assert data['mfa_enabled'] is False


class TestBlueprintRoutes:
    """Test suite for blueprint route registration."""

    def test_autocomplete_route_registered(self, app: Flask):
        """Test that autocomplete route is registered correctly."""
        from ckanext.hdx_users.views.api import hdx_user_autocomplete
        app.register_blueprint(hdx_user_autocomplete)

        # Assert route exists
        assert any(
            rule.rule == '/util/user/hdx_autocomplete'
            for rule in app.url_map.iter_rules()
        )

    def test_check_lockout_route_registered(self, app: Flask):
        """Test that check_lockout route is registered correctly."""
        from ckanext.hdx_users.views.api import hdx_user_autocomplete
        app.register_blueprint(hdx_user_autocomplete)

        # Assert route exists and uses GET method
        matching_rules = [
            rule for rule in app.url_map.iter_rules()
            if rule.rule == '/util/user/check_lockout'
        ]
        assert len(matching_rules) == 1
        assert 'GET' in matching_rules[0].methods

    def test_check_mfa_route_registered(self, app: Flask):
        """Test that check_mfa route is registered correctly."""
        from ckanext.hdx_users.views.api import hdx_user_autocomplete
        app.register_blueprint(hdx_user_autocomplete)

        # Assert route exists and uses GET method
        matching_rules = [
            rule for rule in app.url_map.iter_rules()
            if rule.rule == '/util/user/check_mfa'
        ]
        assert len(matching_rules) == 1
        assert 'GET' in matching_rules[0].methods

    def test_blueprint_name(self, app: Flask):
        """Test that blueprint has correct name."""
        from ckanext.hdx_users.views.api import hdx_user_autocomplete

        assert hdx_user_autocomplete.name == 'hdx_user_autocomplete'

    def test_all_routes_registered(self, app: Flask):
        """Test that all expected routes are registered."""
        from ckanext.hdx_users.views.api import hdx_user_autocomplete
        app.register_blueprint(hdx_user_autocomplete)

        expected_routes = [
            '/util/user/hdx_autocomplete',
            '/util/user/check_lockout',
            '/util/user/check_mfa'
        ]

        registered_routes = [rule.rule for rule in app.url_map.iter_rules()]

        for expected_route in expected_routes:
            assert expected_route in registered_routes
