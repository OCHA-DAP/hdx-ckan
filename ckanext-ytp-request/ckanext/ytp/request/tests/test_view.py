"""
Tests for YTP Request View Module.

This module contains unit tests for the Flask view functions that handle
membership requests in CKAN organizations.
"""

import pytest
from unittest.mock import Mock, patch
from flask import Flask
from werkzeug.exceptions import NotFound

from ckanext.ytp.request.view import (
    show,
    list,
    new,
    reject,
    approve,
    process,
    cancel,
    show_organization,
    membership_cancel,
    _process,
    _get_available_roles,
    _basic_context,
    _save_new,
)


class TestYTPRequestViews:
    """Test suite for YTP Request view functions."""

    @pytest.fixture
    def app(self) -> Flask:
        """
        Create a Flask app for testing.

        :return: Flask application instance
        :rtype: Flask
        """
        app = Flask(__name__)
        app.config['TESTING'] = True
        return app

    @pytest.fixture
    def mock_member(self) -> Mock:
        """
        Create a mock Member object.

        :return: Mocked Member instance
        :rtype: Mock
        """
        member = Mock()
        member.id = 'member-123'
        member.table_id = 'user-456'
        member.state = 'pending'
        member.capacity = 'editor'
        return member

    @pytest.fixture
    def mock_user(self) -> Mock:
        """
        Create a mock User object.

        :return: Mocked User instance
        :rtype: Mock
        """
        user = Mock()
        user.id = 'user-456'
        user.name = 'testuser'
        return user

    @patch('ckanext.ytp.request.view.model')
    @patch('ckanext.ytp.request.view.render')
    @patch('ckanext.ytp.request.view.check_access')
    def test_show_member_request(
        self,
        mock_check_access: Mock,
        mock_render: Mock,
        mock_model: Mock,
        mock_member: Mock,
        mock_user: Mock,
        app: Flask,
    ) -> None:
        """
        Test showing a member request.

        :param mock_check_access: Mocked access checker
        :param mock_render: Mocked render function
        :param mock_model: Mocked model
        :param mock_member: Mocked member
        :param mock_user: Mocked user
        :param app: Flask application
        """
        with app.test_request_context('/?role=editor'):
            from flask import g

            mock_model.Session.query.return_value.get.return_value = mock_member
            g.user = 'testuser'

            with patch('ckanext.ytp.request.view._get_available_roles', return_value=[]):
                show('member-123')

            mock_render.assert_called_once()
            assert 'request/show.html' in str(mock_render.call_args)

    @patch('ckanext.ytp.request.view._')
    @patch('ckanext.ytp.request.view.model')
    @patch('ckanext.ytp.request.view.abort')
    def test_show_member_not_found(self, mock_abort: Mock, mock_model: Mock, mock_translate: Mock, app: Flask) -> None:
        """
        Test showing a non-existent member request.

        :param mock_abort: Mocked abort function
        :param mock_model: Mocked model
        :param mock_translate: Mocked translation function
        :param app: Flask application
        """
        with app.test_request_context():
            mock_translate.return_value = 'Request not found'
            mock_model.Session.query.return_value.get.return_value = None
            mock_abort.side_effect = NotFound('Request not found')

            with pytest.raises(NotFound):
                show('invalid-id')

            mock_abort.assert_called_with(404, 'Request not found')

    @patch('ckanext.ytp.request.view.model')
    @patch('ckanext.ytp.request.view.get_action')
    @patch('ckanext.ytp.request.view.render')
    def test_list_member_requests(self, mock_render: Mock, mock_get_action: Mock, mock_model: Mock, app: Flask) -> None:
        """
        Test listing member requests.

        :param mock_render: Mocked render function
        :param mock_get_action: Mocked action getter
        :param mock_model: Mocked model
        :param app: Flask application
        """
        with app.test_request_context():
            from flask import g

            g.user = 'testuser'
            mock_get_action.return_value.return_value = [
                {'id': '1', 'status': 'pending'},
                {'id': '2', 'status': 'pending'},
            ]

            list()

            mock_render.assert_called_once()
            assert 'request/list.html' in str(mock_render.call_args)

    @patch('ckanext.ytp.request.view.model')
    @patch('ckanext.ytp.request.view.check_access')
    @patch('ckanext.ytp.request.view.h')
    @patch('ckanext.ytp.request.view.config')
    def test_new_request_redirect(
        self,
        mock_config: Mock,
        mock_h: Mock,
        mock_check_access: Mock,
        mock_model: Mock,
        app: Flask,
    ) -> None:
        """
        Test creating a new request with redirect.

        :param mock_config: Mocked config
        :param mock_h: Mocked helpers
        :param mock_check_access: Mocked access checker
        :param mock_model: Mocked model
        :param app: Flask application
        """
        with app.test_request_context(method='GET', query_string=''):
            from flask import g

            g.user = 'testuser'
            mock_config.get.return_value = 'true'

            with patch('ckanext.ytp.request.view._get_available_roles', return_value=[]):
                new()

            mock_h.redirect_to.assert_called_once()

    @patch('ckanext.ytp.request.view.model')
    @patch('ckanext.ytp.request.view.get_action')
    @patch('ckanext.ytp.request.view.h')
    def test_approve_member_request(self, mock_h: Mock, mock_get_action: Mock, mock_model: Mock, app: Flask) -> None:
        """
        Test approving a member request.

        :param mock_h: Mocked helpers
        :param mock_get_action: Mocked action getter
        :param mock_model: Mocked model
        :param app: Flask application
        """
        with app.test_request_context():
            from flask import g

            g.user = 'testuser'

            approve('member-123')

            mock_get_action.assert_called_with('member_request_process')

    @patch('ckanext.ytp.request.view.model')
    @patch('ckanext.ytp.request.view.get_action')
    @patch('ckanext.ytp.request.view.h')
    def test_reject_member_request(self, mock_h: Mock, mock_get_action: Mock, mock_model: Mock, app: Flask) -> None:
        """
        Test rejecting a member request.

        :param mock_h: Mocked helpers
        :param mock_get_action: Mocked action getter
        :param mock_model: Mocked model
        :param app: Flask application
        """
        with app.test_request_context():
            from flask import g

            g.user = 'testuser'

            reject('member-123')

            mock_get_action.assert_called_with('member_request_process')

    @patch('ckanext.ytp.request.view.model')
    def test_process_with_approve(self, mock_model: Mock, app: Flask) -> None:
        """
        Test processing a request with approval.

        :param mock_model: Mocked model
        :param app: Flask application
        """
        with app.test_request_context('/?member_id=member-123&approve=true'):
            from flask import g

            g.user = 'testuser'

            with patch('ckanext.ytp.request.view._process') as mock_process:
                process()

            mock_process.assert_called_once_with('member-123', True)

    @patch('ckanext.ytp.request.view.model')
    def test_process_with_reject(self, mock_model: Mock, app: Flask) -> None:
        """
        Test processing a request with rejection.

        :param mock_model: Mocked model
        :param app: Flask application
        """
        with app.test_request_context('/?member_id=member-123&approve=false'):
            from flask import g

            g.user = 'testuser'

            with patch('ckanext.ytp.request.view._process') as mock_process:
                process()

            mock_process.assert_called_once_with('member-123', False)

    @patch('ckanext.ytp.request.view.model')
    @patch('ckanext.ytp.request.view.get_action')
    @patch('ckanext.ytp.request.view.h')
    def test_cancel_member_request(self, mock_h: Mock, mock_get_action: Mock, mock_model: Mock, app: Flask) -> None:
        """
        Test canceling a member request.

        :param mock_h: Mocked helpers
        :param mock_get_action: Mocked action getter
        :param mock_model: Mocked model
        :param app: Flask application
        """
        with app.test_request_context():
            from flask import g

            g.user = 'testuser'
            mock_get_action.return_value.return_value = None

            cancel('member-123')

            mock_get_action.assert_called_with('member_request_cancel')
            mock_h.redirect_to.assert_called_with('organizations_index')

    @patch('ckanext.ytp.request.view._')
    @patch('ckanext.ytp.request.view.model')
    @patch('ckanext.ytp.request.view.get_action')
    @patch('ckanext.ytp.request.view.abort')
    def test_cancel_not_found(
        self, mock_abort: Mock, mock_get_action: Mock, mock_model: Mock, mock_translate: Mock, app: Flask
    ) -> None:
        """
        Test canceling a non-existent request.

        :param mock_abort: Mocked abort function
        :param mock_get_action: Mocked action getter
        :param mock_model: Mocked model
        :param mock_translate: Mocked translation function
        :param app: Flask application
        """
        from ckan.plugins.toolkit import ObjectNotFound

        with app.test_request_context():
            from flask import g

            g.user = 'testuser'
            mock_translate.return_value = 'Request not found'
            mock_get_action.return_value.side_effect = ObjectNotFound()
            mock_abort.side_effect = NotFound('Request not found')

            with pytest.raises(NotFound):
                cancel('invalid-id')

            mock_abort.assert_called_with(404, 'Request not found')

    @patch('ckanext.ytp.request.view.get_user_member')
    @patch('ckanext.ytp.request.view.h')
    def test_show_organization(self, mock_h: Mock, mock_get_user_member: Mock, mock_member: Mock, app: Flask) -> None:
        """
        Test showing organization membership request.

        :param mock_h: Mocked helpers
        :param mock_get_user_member: Mocked user member getter
        :param mock_member: Mocked member
        :param app: Flask application
        """
        with app.test_request_context():
            mock_get_user_member.return_value = mock_member

            show_organization('org-123')

            mock_h.redirect_to.assert_called_once()

    @patch('ckanext.ytp.request.view._')
    @patch('ckanext.ytp.request.view.get_user_member')
    @patch('ckanext.ytp.request.view.abort')
    def test_show_organization_not_found(
        self, mock_abort: Mock, mock_get_user_member: Mock, mock_translate: Mock, app: Flask
    ) -> None:
        """
        Test showing non-existent organization membership.

        :param mock_abort: Mocked abort function
        :param mock_get_user_member: Mocked user member getter
        :param mock_translate: Mocked translation function
        :param app: Flask application
        """
        with app.test_request_context():
            mock_translate.return_value = 'Request not found'
            mock_get_user_member.return_value = None
            mock_abort.side_effect = NotFound('Request not found')

            with pytest.raises(NotFound):
                show_organization('invalid-org')

            mock_abort.assert_called_with(404, 'Request not found')

    @patch('ckanext.ytp.request.view.model')
    @patch('ckanext.ytp.request.view.get_action')
    @patch('ckanext.ytp.request.view.h')
    def test_membership_cancel(self, mock_h: Mock, mock_get_action: Mock, mock_model: Mock, app: Flask) -> None:
        """
        Test canceling organization membership.

        :param mock_h: Mocked helpers
        :param mock_get_action: Mocked action getter
        :param mock_model: Mocked model
        :param app: Flask application
        """
        with app.test_request_context():
            from flask import g

            g.user = 'testuser'
            mock_get_action.return_value.return_value = None

            membership_cancel('org-123')

            mock_get_action.assert_called_with('member_request_membership_cancel')

    @patch('ckanext.ytp.request.view.model')
    @patch('ckanext.ytp.request.view.get_action')
    @patch('ckanext.ytp.request.view.h')
    def test_process_approve_success(self, mock_h: Mock, mock_get_action: Mock, mock_model: Mock, app: Flask) -> None:
        """
        Test _process function with approval.

        :param mock_h: Mocked helpers
        :param mock_get_action: Mocked action getter
        :param mock_model: Mocked model
        :param app: Flask application
        """
        with app.test_request_context():
            from flask import g

            g.user = 'testuser'
            mock_get_action.return_value.return_value = None

            _process('member-123', True)

            mock_get_action.assert_called_with('member_request_process')

    @patch('ckanext.ytp.request.view.model')
    @patch('ckanext.ytp.request.view.get_action')
    @patch('ckanext.ytp.request.view.config')
    def test_get_available_roles(self, mock_config: Mock, mock_get_action: Mock, mock_model: Mock, app: Flask) -> None:
        """
        Test getting available roles.

        :param mock_config: Mocked config
        :param mock_get_action: Mocked action getter
        :param mock_model: Mocked model
        :param app: Flask application
        """
        with app.test_request_context():
            mock_config.get.return_value = 'true'
            mock_get_action.return_value.return_value = [
                {'value': 'admin', 'text': 'Admin'},
                {'value': 'editor', 'text': 'Editor'},
                {'value': 'member', 'text': 'Member'},
            ]

            roles = _get_available_roles('testuser')

            assert len(roles) == 2
            assert all(role['value'] != 'member' for role in roles)

    @patch('ckanext.ytp.request.view.model')
    def test_basic_context(self, mock_model: Mock, app: Flask) -> None:
        """
        Test creating basic context.

        :param mock_model: Mocked model
        :param app: Flask application
        """
        with app.test_request_context():
            from flask import g

            g.user = 'testuser'

            context = _basic_context()

            assert context['user'] == 'testuser'
            assert 'model' in context
            assert 'session' in context

    @patch('ckanext.ytp.request.view._')
    @patch('ckanext.ytp.request.view.model')
    @patch('ckanext.ytp.request.view.get_action')
    @patch('ckanext.ytp.request.view.h')
    @patch('ckanext.ytp.request.view.config')
    @patch('ckanext.ytp.request.view.clean_dict')
    @patch('ckanext.ytp.request.view.dict_fns')
    @patch('ckanext.ytp.request.view.parse_params')
    def test_save_new_with_redirect(
        self,
        mock_parse_params: Mock,
        mock_dict_fns: Mock,
        mock_clean_dict: Mock,
        mock_config: Mock,
        mock_h: Mock,
        mock_get_action: Mock,
        mock_model: Mock,
        mock_translate: Mock,
        app: Flask,
    ) -> None:
        """
        Test saving a new request with redirect.

        :param mock_parse_params: Mocked param parser
        :param mock_dict_fns: Mocked dictionary functions
        :param mock_clean_dict: Mocked clean dict function
        :param mock_config: Mocked config
        :param mock_h: Mocked helpers
        :param mock_get_action: Mocked action getter
        :param mock_model: Mocked model
        :param mock_translate: Mocked translation function
        :param app: Flask application
        """
        with app.test_request_context(
            method='POST',
            data={'organization': 'org-123', 'role': 'editor'},
            headers={'Referer': 'http://example.com/source'},
        ):
            from flask import g

            g.user = 'testuser'
            context = {'save': True}

            # Mock DataError as a proper exception class
            mock_dict_fns.DataError = type('DataError', (Exception,), {})

            mock_translate.return_value = 'Thank you for your request. The organisation admins were notified.'
            mock_parse_params.return_value = {'organization': 'org-123'}
            mock_dict_fns.unflatten.return_value = {'organization': 'org-123'}
            mock_clean_dict.return_value = {'organization': 'org-123'}
            mock_config.get.return_value = 'true'
            mock_get_action.return_value.return_value = {'id': 'member-123'}

            _save_new(context)

            mock_h.flash_success.assert_called_once()
            mock_h.redirect_to.assert_called()

    @patch('ckanext.ytp.request.view._')
    @patch('ckanext.ytp.request.view.model')
    @patch('ckanext.ytp.request.view.get_action')
    @patch('ckanext.ytp.request.view.h')
    @patch('ckanext.ytp.request.view.clean_dict')
    @patch('ckanext.ytp.request.view.dict_fns')
    @patch('ckanext.ytp.request.view.parse_params')
    @patch('ckanext.ytp.request.view.tuplize_dict')
    def test_save_new_validation_error(
        self,
        mock_tuplize_dict: Mock,
        mock_parse_params: Mock,
        mock_dict_fns: Mock,
        mock_clean_dict: Mock,
        mock_h: Mock,
        mock_get_action: Mock,
        mock_model: Mock,
        mock_translate: Mock,
        app: Flask,
    ) -> None:
        """
        Test saving a new request with validation error.

        :param mock_tuplize_dict: Mocked tuplize_dict function
        :param mock_parse_params: Mocked param parser
        :param mock_dict_fns: Mocked dictionary functions
        :param mock_clean_dict: Mocked clean dict function
        :param mock_h: Mocked helpers
        :param mock_get_action: Mocked action getter
        :param mock_model: Mocked model
        :param mock_translate: Mocked translation function
        :param app: Flask application
        """
        from ckan.logic import ValidationError

        with app.test_request_context(method='POST', data={}):
            from flask import g

            g.user = 'testuser'
            context = {'save': True}

            # Mock DataError as a proper exception class
            mock_dict_fns.DataError = type('DataError', (Exception,), {})

            mock_translate.return_value = 'Validation error'
            mock_parse_params.return_value = {}
            mock_tuplize_dict.return_value = {}
            mock_dict_fns.unflatten.return_value = {'organization': 'org-123'}
            mock_clean_dict.return_value = {'organization': 'org-123'}
            mock_get_action.return_value.side_effect = ValidationError({})

            with patch('ckanext.ytp.request.view.new') as mock_new:
                mock_new.return_value = 'rendered_template'
                result = _save_new(context)

                # Validation error should call new() function
                mock_new.assert_called_once()
                mock_h.flash_error.assert_called_once()
                assert result == 'rendered_template'
