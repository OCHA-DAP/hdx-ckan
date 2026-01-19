import pytest
from unittest.mock import Mock, patch, MagicMock
from werkzeug.datastructures import ImmutableMultiDict

import ckan.plugins.toolkit as tk

NotFound = tk.ObjectNotFound
NotAuthorized = tk.NotAuthorized


@pytest.fixture(scope='module', autouse=True)
def mock_g_module():
    """Mock Flask's g object at module level before imports"""
    with patch.dict('sys.modules', {'flask': MagicMock()}):
        import sys
        if 'flask' in sys.modules:
            mock_g = MagicMock()
            sys.modules['flask'].g = mock_g
        yield


class TestDatasetRequestAccessLogic:
    @pytest.fixture
    def mock_context(self):
        """Mock CKAN context"""
        return {
            'model': Mock(),
            'session': Mock(),
            'user': 'test_user',
            'auth_user_obj': Mock(id='user123', email='testuser@example.com', name='Test User'),
        }

    @pytest.fixture
    def mock_request(self):
        """Mock Flask request object"""
        request = Mock()
        request.form = ImmutableMultiDict(
            [
                ('package_id', 'dataset-123'),
                ('sender_name', 'John Doe'),
                ('email_address', 'john@example.com'),
                ('message_content', 'Please provide access'),
            ]
        )
        return request

    @pytest.fixture
    def sample_package_dict(self):
        """Sample package dictionary"""
        return {
            'id': 'dataset-123',
            'name': 'test-dataset',
            'title': 'Test Dataset',
            'maintainer': 'maintainer123',
            'owner_org': 'org-456',
            'organization': {'title': 'Test Organization'},
        }

    @pytest.fixture
    def sample_maintainer_dict(self):
        """Sample maintainer user dictionary"""
        return {
            'id': 'maintainer123',
            'name': 'maintainer',
            'fullname': 'Dataset Maintainer',
            'email': 'maintainer@example.com',
            'display_name': 'Dataset Maintainer',
        }

    def test_init(self, mock_context, mock_request):
        """Test initialization of DatasetRequestAccessLogic"""
        from ckanext.hdx_package.controller_logic.dataset_request_access_logic import DatasetRequestAccessLogic

        logic = DatasetRequestAccessLogic(mock_context, mock_request)

        assert logic.context == mock_context
        assert logic.request == mock_request
        assert logic.form == mock_request.form
        assert logic.schema is not None

    def test_read(self, mock_context, mock_request):
        """Test read method returns cleaned data dict"""
        from ckanext.hdx_package.controller_logic.dataset_request_access_logic import DatasetRequestAccessLogic

        logic = DatasetRequestAccessLogic(mock_context, mock_request)

        result = logic.read()

        assert isinstance(result, dict)
        assert 'package_id' in result
        assert result['package_id'] == 'dataset-123'

    def test_validate_success(self, mock_context, mock_request):
        """Test validate method with valid data"""
        from ckanext.hdx_package.controller_logic.dataset_request_access_logic import DatasetRequestAccessLogic

        logic = DatasetRequestAccessLogic(mock_context, mock_request)
        data_dict = {
            'package_id': 'dataset-123',
            'sender_name': 'John Doe',
            'email_address': 'john@example.com',
            'message_content': 'Test message',
        }

        with patch('ckanext.hdx_package.controller_logic.dataset_request_access_logic.validate') as mock_validate:
            mock_validate.return_value = (data_dict, None)

            result = logic.validate(data_dict)

            assert result == (data_dict, None)
            mock_validate.assert_called_once()

    def test_validate_with_errors(self, mock_context, mock_request):
        """Test validate method with validation errors"""
        from ckanext.hdx_package.controller_logic.dataset_request_access_logic import DatasetRequestAccessLogic

        logic = DatasetRequestAccessLogic(mock_context, mock_request)
        data_dict = {'package_id': ''}

        with patch('ckanext.hdx_package.controller_logic.dataset_request_access_logic.validate') as mock_validate:
            errors = {'package_id': ['Missing value']}
            mock_validate.return_value = (data_dict, errors)

            result = logic.validate(data_dict)

            assert result == (data_dict, errors)

    @patch('ckanext.hdx_package.controller_logic.dataset_request_access_logic.get_action')
    def test_send_request_no_maintainer(self, mock_get_action, mock_context, mock_request):
        """Test send_request returns error when maintainer is None"""
        from ckanext.hdx_package.controller_logic.dataset_request_access_logic import DatasetRequestAccessLogic

        mock_package_show = Mock(return_value={'id': 'dataset-123', 'maintainer': None})

        def get_action_side_effect(action_name):
            if action_name == 'package_show':
                return mock_package_show
            return Mock()

        mock_get_action.side_effect = get_action_side_effect

        logic = DatasetRequestAccessLogic(mock_context, mock_request)

        success, message = logic.send_request()

        assert success is False
        assert message == 'Dataset maintainer email not found.'

    def test_send_request_success_with_maintainer(
        self,
        mock_context,
        mock_request,
        sample_package_dict,
        sample_maintainer_dict,
    ):
        """Test send_request successfully sends emails when maintainer exists"""
        from ckanext.hdx_package.controller_logic.dataset_request_access_logic import DatasetRequestAccessLogic

        # Create mock_g before using it in patch
        mock_g = MagicMock()
        mock_g.user = 'test_user'
        mock_g.userobj = mock_context['auth_user_obj']

        with (
            patch('ckanext.hdx_package.controller_logic.dataset_request_access_logic.get_action') as mock_get_action,
            patch(
                'ckanext.hdx_package.controller_logic.dataset_request_access_logic._send_email_to_maintainer'
            ) as mock_send_maintainer,
            patch(
                'ckanext.hdx_package.controller_logic.dataset_request_access_logic._send_email_to_requester'
            ) as mock_send_requester,
            patch(
                'ckanext.hdx_package.controller_logic.dataset_request_access_logic.process_extras_fields'
            ) as mock_process_extras,
            patch('ckanext.hdx_package.controller_logic.dataset_request_access_logic.g', new=mock_g),
        ):
            mock_request_create = Mock()
            mock_package_show = Mock(return_value=sample_package_dict)
            mock_user_show = Mock(return_value=sample_maintainer_dict)
            mock_org_show = Mock(return_value={'id': 'org-456', 'name': 'test-org'})
            mock_org_list = Mock(return_value=[])
            mock_notification_create = Mock()
            mock_increment_counters = Mock()

            def get_action_side_effect(action_name):
                actions = {
                    'requestdata_request_create': mock_request_create,
                    'package_show': mock_package_show,
                    'user_show': mock_user_show,
                    'organization_show': mock_org_show,
                    'organization_list_for_user': mock_org_list,
                    'requestdata_notification_create': mock_notification_create,
                    'requestdata_increment_request_data_counters': mock_increment_counters,
                }
                return actions[action_name]

            mock_get_action.side_effect = get_action_side_effect
            mock_process_extras.return_value = '[]'

            logic = DatasetRequestAccessLogic(mock_context, mock_request)

            success, message = logic.send_request()

            assert success is True
            assert message == 'Email message was successfully sent.'
            mock_send_maintainer.assert_called_once()
            mock_send_requester.assert_called_once()
            mock_notification_create.assert_called_once()
            mock_increment_counters.assert_called_once()

    def test_send_request_maintainer_not_found_uses_admins(
        self,
        mock_context,
        mock_request,
        sample_package_dict,
    ):
        """Test send_request falls back to org admins when maintainer not found"""
        from ckanext.hdx_package.controller_logic.dataset_request_access_logic import DatasetRequestAccessLogic

        # Create mock_g before using it in patch
        mock_g = MagicMock()
        mock_g.user = 'test_user'
        mock_g.userobj = mock_context['auth_user_obj']

        with (
            patch('ckanext.hdx_package.controller_logic.dataset_request_access_logic.get_action') as mock_get_action,
            patch(
                'ckanext.hdx_package.controller_logic.dataset_request_access_logic._send_email_to_maintainer'
            ) as mock_send_maintainer,
            patch(
                'ckanext.hdx_package.controller_logic.dataset_request_access_logic._send_email_to_requester'
            ) as mock_send_requester,
            patch(
                'ckanext.hdx_package.controller_logic.dataset_request_access_logic.process_extras_fields'
            ) as mock_process_extras,
            patch(
                'ckanext.hdx_package.controller_logic.dataset_request_access_logic._org_admins_for_dataset'
            ) as mock_org_admins,
            patch('ckanext.hdx_package.controller_logic.dataset_request_access_logic.g', new=mock_g),
        ):
            mock_request_create = Mock()
            mock_package_show = Mock(return_value=sample_package_dict)
            mock_user_show = Mock(side_effect=NotFound)
            mock_org_show = Mock(return_value={'id': 'org-456', 'name': 'test-org'})
            mock_org_list = Mock(return_value=[])
            mock_notification_create = Mock()
            mock_increment_counters = Mock()

            admin_list = [
                {'fullname': 'Admin One', 'email': 'admin1@example.com'},
                {'fullname': 'Admin Two', 'email': 'admin2@example.com'},
            ]
            mock_org_admins.return_value = admin_list

            def get_action_side_effect(action_name):
                actions = {
                    'requestdata_request_create': mock_request_create,
                    'package_show': mock_package_show,
                    'user_show': mock_user_show,
                    'organization_show': mock_org_show,
                    'organization_list_for_user': mock_org_list,
                    'requestdata_notification_create': mock_notification_create,
                    'requestdata_increment_request_data_counters': mock_increment_counters,
                }
                return actions[action_name]

            mock_get_action.side_effect = get_action_side_effect
            mock_process_extras.return_value = '[]'

            logic = DatasetRequestAccessLogic(mock_context, mock_request)

            success, message = logic.send_request()

            assert success is True
            mock_org_admins.assert_called_once()
            mock_send_maintainer.assert_called_once()
            # Verify admins were used as recipients
            call_args = mock_send_maintainer.call_args[0]
            recipients = call_args[4]  # recipients is the 5th argument
            assert len(recipients) == 2
            assert recipients[0]['email'] == 'admin1@example.com'


class TestOrgAdminsForDataset:
    @pytest.fixture
    def mock_context(self):
        return {'model': Mock(), 'session': Mock(), 'user': 'test_user'}

    @pytest.fixture
    def sample_org_dict(self):
        """Sample organization with users"""
        return {
            'id': 'org-456',
            'name': 'test-org',
            'users': [
                {'id': 'user1', 'capacity': 'admin'},
                {'id': 'user2', 'capacity': 'editor'},
                {'id': 'user3', 'capacity': 'admin'},
                {'id': 'user4', 'capacity': 'member'},
            ],
        }

    @patch('ckanext.hdx_package.controller_logic.dataset_request_access_logic.model')
    @patch('ckanext.hdx_package.controller_logic.dataset_request_access_logic.get_action')
    def test_org_admins_for_dataset_returns_admins_only(
        self, mock_get_action, mock_model, mock_context, sample_org_dict
    ):
        """Test _org_admins_for_dataset returns only admin users"""
        from ckanext.hdx_package.controller_logic.dataset_request_access_logic import _org_admins_for_dataset

        mock_package_show = Mock(return_value={'id': 'dataset-123', 'name': 'test-dataset', 'owner_org': 'org-456'})
        mock_org_show = Mock(return_value=sample_org_dict)

        def get_action_side_effect(action_name):
            if action_name == 'package_show':
                return mock_package_show
            elif action_name == 'organization_show':
                return mock_org_show

        mock_get_action.side_effect = get_action_side_effect

        def user_get_side_effect(user_id):
            users = {
                'user1': Mock(id='user1', email='admin1@example.com', fullname='Admin One', name='admin1'),
                'user3': Mock(id='user3', email='admin3@example.com', fullname='Admin Three', name='admin3'),
            }
            return users.get(user_id)

        mock_model.User.get.side_effect = user_get_side_effect

        result = _org_admins_for_dataset(mock_context, 'test-dataset')

        assert len(result) == 2
        assert result[0]['email'] == 'admin1@example.com'
        assert result[0]['fullname'] == 'Admin One'
        assert result[1]['email'] == 'admin3@example.com'
        assert result[1]['fullname'] == 'Admin Three'

    @patch('ckanext.hdx_package.controller_logic.dataset_request_access_logic.model')
    @patch('ckanext.hdx_package.controller_logic.dataset_request_access_logic.get_action')
    def test_org_admins_for_dataset_uses_name_if_no_fullname(self, mock_get_action, mock_model, mock_context):
        """Test _org_admins_for_dataset uses name when fullname is None"""
        from ckanext.hdx_package.controller_logic.dataset_request_access_logic import _org_admins_for_dataset

        mock_package_show = Mock(return_value={'owner_org': 'org-456'})
        org_dict = {'id': 'org-456', 'users': [{'id': 'user1', 'capacity': 'admin'}]}
        mock_org_show = Mock(return_value=org_dict)

        def get_action_side_effect(action_name):
            if action_name == 'package_show':
                return mock_package_show
            elif action_name == 'organization_show':
                return mock_org_show

        mock_get_action.side_effect = get_action_side_effect

        mock_user = Mock()
        mock_user.id = 'user1'
        mock_user.email = 'admin@example.com'
        mock_user.fullname = None
        mock_user.name = 'admin_username'
        mock_model.User.get.return_value = mock_user

        result = _org_admins_for_dataset(mock_context, 'test-dataset')

        assert len(result) == 1
        assert result[0]['email'] == 'admin@example.com'
        assert result[0]['fullname'] == 'admin_username'

    @patch('ckanext.hdx_package.controller_logic.dataset_request_access_logic.get_action')
    def test_org_admins_for_dataset_empty_when_no_admins(self, mock_get_action, mock_context):
        """Test _org_admins_for_dataset returns empty list when no admins"""
        from ckanext.hdx_package.controller_logic.dataset_request_access_logic import _org_admins_for_dataset

        mock_package_show = Mock(return_value={'owner_org': 'org-456'})
        org_dict = {
            'id': 'org-456',
            'users': [{'id': 'user1', 'capacity': 'editor'}, {'id': 'user2', 'capacity': 'member'}],
        }
        mock_org_show = Mock(return_value=org_dict)

        def get_action_side_effect(action_name):
            if action_name == 'package_show':
                return mock_package_show
            elif action_name == 'organization_show':
                return mock_org_show

        mock_get_action.side_effect = get_action_side_effect

        result = _org_admins_for_dataset(mock_context, 'test-dataset')

        assert len(result) == 0


class TestEmailFunctions:
    @pytest.fixture
    def sample_package_dict(self):
        return {
            'name': 'test-dataset',
            'title': 'Test Dataset',
            'owner_org': 'org-456',
            'organization': {'title': 'Test Organization'},
        }

    @patch('ckanext.hdx_package.controller_logic.dataset_request_access_logic.h')
    @patch('ckanext.hdx_package.controller_logic.dataset_request_access_logic.hdx_mailer')
    def test_send_email_to_requester(self, mock_mailer, mock_h, sample_package_dict):
        """Test _send_email_to_requester sends email with correct data"""
        from ckanext.hdx_package.controller_logic.dataset_request_access_logic import _send_email_to_requester

        mock_h.url_for.return_value = 'http://example.com/dataset/test-dataset'

        _send_email_to_requester(
            sender_name='John Doe',
            sender_email='john@example.com',
            message='Please provide access',
            user_email='user@example.com',
            pkg_dict=sample_package_dict,
        )

        mock_mailer.mail_recipient.assert_called_once()
        call_args = mock_mailer.mail_recipient.call_args

        recipients = call_args[0][0]
        assert len(recipients) == 1
        assert recipients[0]['email'] == 'john@example.com'
        assert recipients[0]['display_name'] == 'John Doe'

        subject = call_args[0][1]
        assert subject == 'Request for access to metadata-only dataset'

        email_data = call_args[0][2]
        assert email_data['user_fullname'] == 'John Doe'
        assert email_data['msg'] == 'Please provide access'
        assert email_data['dataset_title'] == 'Test Dataset'

    @patch('ckanext.hdx_package.controller_logic.dataset_request_access_logic.h')
    @patch('ckanext.hdx_package.controller_logic.dataset_request_access_logic.hdx_mailer')
    def test_send_email_to_maintainer(self, mock_mailer, mock_h, sample_package_dict):
        """Test _send_email_to_maintainer sends email with correct data"""
        from ckanext.hdx_package.controller_logic.dataset_request_access_logic import _send_email_to_maintainer

        mock_h.url_for.side_effect = ['http://example.com/dataset/test-dataset', 'http://example.com/requests/org-456']

        maintainer_dict = {
            'fullname': 'Dataset Maintainer',
            'email': 'maintainer@example.com',
            'display_name': 'Maintainer Display',
        }

        recipients = [{'display_name': 'Maintainer Display', 'email': 'maintainer@example.com'}]

        _send_email_to_maintainer(
            sender_name='John Doe',
            message='Please provide access',
            user_email='john@example.com',
            extras=[],
            recipients=recipients,
            maintainer_dict=maintainer_dict,
            pkg_dict=sample_package_dict,
        )

        mock_mailer.mail_recipient.assert_called_once()
        call_args = mock_mailer.mail_recipient.call_args

        sent_recipients = call_args[0][0]
        assert sent_recipients == recipients

        subject = call_args[0][1]
        assert 'John Doe' in subject
        assert 'Test Dataset' in subject

        email_data = call_args[0][2]
        assert email_data['user_fullname'] == 'John Doe'
        assert email_data['user_email'] == 'john@example.com'
        assert email_data['maintainer_fullname'] == 'Maintainer Display'

    @patch('ckanext.hdx_package.controller_logic.dataset_request_access_logic.h')
    @patch('ckanext.hdx_package.controller_logic.dataset_request_access_logic.hdx_mailer')
    def test_send_email_to_maintainer_no_maintainer_dict(self, mock_mailer, mock_h, sample_package_dict):
        """Test _send_email_to_maintainer with no maintainer_dict uses default"""
        from ckanext.hdx_package.controller_logic.dataset_request_access_logic import _send_email_to_maintainer

        mock_h.url_for.side_effect = ['http://example.com/dataset/test-dataset', 'http://example.com/requests/org-456']

        recipients = [{'display_name': 'Admin', 'email': 'admin@example.com'}]

        _send_email_to_maintainer(
            sender_name='John Doe',
            message='Please provide access',
            user_email='john@example.com',
            extras=[],
            recipients=recipients,
            maintainer_dict={},
            pkg_dict=sample_package_dict,
        )

        call_args = mock_mailer.mail_recipient.call_args
        email_data = call_args[0][2]
        assert email_data['maintainer_fullname'] == 'HDX user'

    @patch('ckanext.hdx_package.controller_logic.dataset_request_access_logic.h')
    @patch('ckanext.hdx_package.controller_logic.dataset_request_access_logic.hdx_mailer')
    def test_send_email_to_maintainer_with_extras(self, mock_mailer, mock_h, sample_package_dict):
        """Test _send_email_to_maintainer includes extras in email data"""
        from ckanext.hdx_package.controller_logic.dataset_request_access_logic import _send_email_to_maintainer

        mock_h.url_for.side_effect = ['http://example.com/dataset/test-dataset', 'http://example.com/requests/org-456']

        extras = [{'key': 'organization', 'value': 'Test Org'}, {'key': 'purpose', 'value': 'Research'}]

        recipients = [{'display_name': 'Maintainer', 'email': 'maintainer@example.com'}]
        maintainer_dict = {'fullname': 'Maintainer'}

        _send_email_to_maintainer(
            sender_name='John Doe',
            message='Please provide access',
            user_email='john@example.com',
            extras=extras,
            recipients=recipients,
            maintainer_dict=maintainer_dict,
            pkg_dict=sample_package_dict,
        )

        call_args = mock_mailer.mail_recipient.call_args
        email_data = call_args[0][2]
        assert email_data['extras'] == extras
