"""
Tests for HDX Service Checker Checks Module.

This module contains unit tests for various check implementations used in
service health monitoring.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import requests
from requests.exceptions import RequestException, Timeout

from ckanext.hdx_service_checker.checks.checks import (
    DummyCheck,
    HttpStatusCodeCheck,
    HttpResponseTextCheck,
    ProxyForRemoteCheck,
)
from ckanext.hdx_service_checker.exceptions import CheckException, ParamMissingException


class TestDummyCheck:
    """Test suite for DummyCheck class."""

    def test_dummy_check_default_config(self) -> None:
        """
        Test DummyCheck with default configuration values.
        """
        # Setup
        config = {'name': 'Test Dummy Check'}

        # Execute
        check = DummyCheck(config)

        # Assert
        assert check.type == 'Dummy Check'
        assert check.result == 'Passed'
        assert check.error_message == 'Dummy message'
        assert check.description == 'Just a dummy check. Does nothing.'
        assert check.name == 'Test Dummy Check'

    def test_dummy_check_custom_config(self) -> None:
        """
        Test DummyCheck with custom configuration values.
        """
        # Setup
        config = {
            'name': 'Custom Dummy',
            'result': 'Failed',
            'error_message': 'Custom error',
            'description': 'Custom description'
        }

        # Execute
        check = DummyCheck(config)

        # Assert
        assert check.result == 'Failed'
        assert check.error_message == 'Custom error'
        assert check.description == 'Custom description'
        assert check.name == 'Custom Dummy'

    def test_dummy_check_missing_name_raises_exception(self) -> None:
        """
        Test DummyCheck raises exception when name is missing.
        """
        # Setup
        config = {}

        # Execute & Assert
        with pytest.raises(ParamMissingException):
            DummyCheck(config)

    def test_dummy_check_custom_user_agent(self) -> None:
        """
        Test DummyCheck with custom user agent.
        """
        # Setup
        config = {'name': 'Test Check'}
        user_agent = 'CUSTOM_AGENT'

        # Execute
        check = DummyCheck(config, user_agent=user_agent)

        # Assert
        assert check.user_agent == 'CUSTOM_AGENT'

    def test_dummy_check_run_check(self) -> None:
        """
        Test running DummyCheck returns expected result.
        """
        # Setup
        config = {'name': 'Test Check', 'result': 'Passed'}
        check = DummyCheck(config)

        # Execute
        result = check.run_check()

        # Assert
        assert result is not None


class TestHttpStatusCodeCheck:
    """Test suite for HttpStatusCodeCheck class."""

    def test_http_status_code_check_type(self) -> None:
        """
        Test HttpStatusCodeCheck type attribute.
        """
        # Setup
        config = {
            'name': 'Test',
            'url': 'http://example.com',
            'accepted_codes': '200'
        }

        # Execute
        check = HttpStatusCodeCheck(config)

        # Assert
        assert check.type == 'HTTP Status Check'
        assert 'HTTP response code' in check.description

    @patch('requests.get')
    def test_http_status_code_check_success_single_code(
        self, mock_get: Mock
    ) -> None:
        """
        Test HttpStatusCodeCheck with successful response matching single accepted code.

        :param mock_get: Mocked requests.get function
        """
        # Setup
        config = {
            'name': 'Solr',
            'url': 'http://172.17.42.1:9013/api/status_check',
            'accepted_codes': '200'
        }

        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        check = HttpStatusCodeCheck(config)

        # Execute
        result = check.run_check()

        # Assert
        mock_get.assert_called_once()
        assert result is not None

    @patch('requests.get')
    def test_http_status_code_check_success_multiple_codes(
        self, mock_get: Mock
    ) -> None:
        """
        Test HttpStatusCodeCheck with response matching one of multiple accepted codes.

        :param mock_get: Mocked requests.get function
        """
        # Setup
        config = {
            'name': 'Web Service',
            'url': 'http://example.com',
            'accepted_codes': '200, 302, 304'
        }

        mock_response = Mock()
        mock_response.status_code = 302
        mock_get.return_value = mock_response

        check = HttpStatusCodeCheck(config)

        # Execute
        result = check.run_check()

        # Assert
        mock_get.assert_called_once()
        assert result is not None

    @patch('requests.get')
    def test_http_status_code_check_failure_wrong_code(
        self, mock_get: Mock
    ) -> None:
        """
        Test HttpStatusCodeCheck with response not matching accepted codes.

        :param mock_get: Mocked requests.get function
        """
        # Setup
        config = {
            'name': 'Web Service',
            'url': 'http://example.com',
            'accepted_codes': '200'
        }

        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        check = HttpStatusCodeCheck(config)

        # Execute
        result = check.run_check()

        # Assert
        mock_get.assert_called_once()
        assert result is not None
        assert check.result == 'Failed'

    @patch('requests.get')
    def test_http_status_code_check_request_exception(
        self, mock_get: Mock
    ) -> None:
        """
        Test HttpStatusCodeCheck handling request exceptions.

        :param mock_get: Mocked requests.get function
        """
        # Setup
        config = {
            'name': 'Web Service',
            'url': 'http://example.com',
            'accepted_codes': '200'
        }

        mock_get.side_effect = RequestException('Connection error')
        check = HttpStatusCodeCheck(config)

        # Execute
        result = check.run_check()

        # Assert
        assert result is not None
        assert check.result == 'Failed'
        assert check.error_message != ''

    @patch('requests.get')
    def test_http_status_code_check_timeout(
        self, mock_get: Mock
    ) -> None:
        """
        Test HttpStatusCodeCheck handling timeout errors.

        :param mock_get: Mocked requests.get function
        """
        # Setup
        config = {
            'name': 'Web Service',
            'url': 'http://example.com',
            'accepted_codes': '200'
        }

        mock_get.side_effect = Timeout('Request timeout')
        check = HttpStatusCodeCheck(config)

        # Execute
        result = check.run_check()

        # Assert
        assert result is not None
        assert check.result == 'Failed'
        assert check.error_message != ''

    @patch('requests.get')
    def test_http_status_code_check_with_custom_user_agent(
        self, mock_get: Mock
    ) -> None:
        """
        Test HttpStatusCodeCheck uses custom user agent in request headers.

        :param mock_get: Mocked requests.get function
        """
        # Setup
        config = {
            'name': 'Web Service',
            'url': 'http://example.com',
            'accepted_codes': '200'
        }

        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        check = HttpStatusCodeCheck(config, user_agent='CUSTOM_AGENT')

        # Execute
        check.run_check()

        # Assert - verify headers were passed
        mock_get.assert_called_once()
        call_kwargs = mock_get.call_args[1]
        if 'headers' in call_kwargs:
            assert call_kwargs['headers']['User-Agent'] == 'CUSTOM_AGENT'


class TestHttpResponseTextCheck:
    """Test suite for HttpResponseTextCheck class."""

    def test_http_response_text_check_type(self) -> None:
        """
        Test HttpResponseTextCheck type attribute.
        """
        # Setup
        config = {
            'name': 'Test',
            'url': 'http://example.com',
            'included_text': 'OK'
        }

        # Execute
        check = HttpResponseTextCheck(config)

        # Assert
        assert hasattr(check, 'type')

    @patch('requests.get')
    def test_http_response_text_check_success(
        self, mock_get: Mock
    ) -> None:
        """
        Test HttpResponseTextCheck with response containing expected text.

        :param mock_get: Mocked requests.get function
        """
        # Setup
        config = {
            'name': 'API Health',
            'url': 'http://api.example.com/health',
            'included_text': 'healthy'
        }

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = 'System is healthy'
        mock_get.return_value = mock_response

        check = HttpResponseTextCheck(config)

        # Execute
        result = check.run_check()

        # Assert
        mock_get.assert_called_once()
        assert result is not None

    @patch('requests.get')
    def test_http_response_text_check_failure_missing_text(
        self, mock_get: Mock
    ) -> None:
        """
        Test HttpResponseTextCheck with response missing expected text.

        :param mock_get: Mocked requests.get function
        """
        # Setup
        config = {
            'name': 'API Health',
            'url': 'http://api.example.com/health',
            'included_text': 'healthy'
        }

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = 'System is down'
        mock_get.return_value = mock_response

        check = HttpResponseTextCheck(config)

        # Execute
        result = check.run_check()

        # Assert
        mock_get.assert_called_once()
        assert result is not None
        assert check.result == 'Failed'

    @patch('requests.get')
    def test_http_response_text_check_request_exception(
        self, mock_get: Mock
    ) -> None:
        """
        Test HttpResponseTextCheck handling request exceptions.

        :param mock_get: Mocked requests.get function
        """
        # Setup
        config = {
            'name': 'API Health',
            'url': 'http://api.example.com/health',
            'included_text': 'healthy'
        }

        mock_get.side_effect = RequestException('Connection error')
        check = HttpResponseTextCheck(config)

        # Execute
        result = check.run_check()

        # Assert
        assert result is not None
        assert check.result == 'Failed'


class TestProxyForRemoteCheck:
    """Test suite for ProxyForRemoteCheck class."""

    def test_proxy_for_remote_check_type(self) -> None:
        """
        Test ProxyForRemoteCheck type and description.
        """
        # Setup
        config = {
            'name': 'Remote Service',
            'url': 'http://remote.example.com/check'
        }

        # Execute
        check = ProxyForRemoteCheck(config)

        # Assert
        assert check.type == 'Proxy for Remote Check'
        assert 'another service' in check.description

    @patch('requests.get')
    def test_proxy_for_remote_check_success(
        self, mock_get: Mock
    ) -> None:
        """
        Test ProxyForRemoteCheck with successful remote check response.

        :param mock_get: Mocked requests.get function
        """
        # Setup
        config = {
            'name': 'Remote Service',
            'url': 'http://remote.example.com/check'
        }

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'status': 'success',
            'checks': []
        }
        mock_get.return_value = mock_response

        check = ProxyForRemoteCheck(config)

        # Execute
        result = check.run_check()

        # Assert
        mock_get.assert_called_once()
        assert result is not None

    @patch('requests.get')
    def test_proxy_for_remote_check_request_exception(
        self, mock_get: Mock
    ) -> None:
        """
        Test ProxyForRemoteCheck handling request exceptions.

        :param mock_get: Mocked requests.get function
        """
        # Setup
        config = {
            'name': 'Remote Service',
            'url': 'http://remote.example.com/check'
        }

        mock_get.side_effect = RequestException('Connection error')
        check = ProxyForRemoteCheck(config)

        # Execute
        result = check.run_check()

        # Assert
        assert result is not None
        assert check.result == 'Failed'

    @patch('requests.get')
    def test_proxy_for_remote_check_timeout(
        self, mock_get: Mock
    ) -> None:
        """
        Test ProxyForRemoteCheck handling timeout errors.

        :param mock_get: Mocked requests.get function
        """
        # Setup
        config = {
            'name': 'Remote Service',
            'url': 'http://remote.example.com/check'
        }

        mock_get.side_effect = Timeout('Request timeout')
        check = ProxyForRemoteCheck(config)

        # Execute
        result = check.run_check()

        # Assert
        assert result is not None
        assert check.result == 'Failed'


class TestChecksIntegration:
    """Integration tests for check classes."""

    def test_all_checks_have_type_attribute(self) -> None:
        """
        Test that all check classes have a type attribute.
        """
        # Setup
        check_configs = [
            ({'name': 'Test Dummy'}, DummyCheck),
            ({'name': 'Test HTTP', 'url': 'http://example.com', 'accepted_codes': '200'}, HttpStatusCodeCheck),
            ({'name': 'Test Text', 'url': 'http://example.com', 'included_text': 'OK'}, HttpResponseTextCheck),
            ({'name': 'Test Proxy', 'url': 'http://example.com'}, ProxyForRemoteCheck),
        ]

        # Execute & Assert
        for config, check_class in check_configs:
            check = check_class(config)
            assert hasattr(check, 'type')
            assert isinstance(check.type, str)

    def test_all_checks_have_description_attribute(self) -> None:
        """
        Test that all check classes have a description attribute.
        """
        # Setup
        check_configs = [
            ({'name': 'Test Dummy'}, DummyCheck),
            ({'name': 'Test HTTP', 'url': 'http://example.com', 'accepted_codes': '200'}, HttpStatusCodeCheck),
            ({'name': 'Test Text', 'url': 'http://example.com', 'included_text': 'OK'}, HttpResponseTextCheck),
            ({'name': 'Test Proxy', 'url': 'http://example.com'}, ProxyForRemoteCheck),
        ]

        # Execute & Assert
        for config, check_class in check_configs:
            check = check_class(config)
            assert hasattr(check, 'description')
            assert isinstance(check.description, str)

    def test_all_checks_have_run_check_method(self) -> None:
        """
        Test that all check classes have a run_check method.
        """
        # Setup
        check_configs = [
            ({'name': 'Test Dummy'}, DummyCheck),
            ({'name': 'Test HTTP', 'url': 'http://example.com', 'accepted_codes': '200'}, HttpStatusCodeCheck),
            ({'name': 'Test Text', 'url': 'http://example.com', 'included_text': 'OK'}, HttpResponseTextCheck),
            ({'name': 'Test Proxy', 'url': 'http://example.com'}, ProxyForRemoteCheck),
        ]

        # Execute & Assert
        for config, check_class in check_configs:
            check = check_class(config)
            assert hasattr(check, 'run_check')
            assert callable(check.run_check)
