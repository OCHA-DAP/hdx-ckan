"""Test module for hdx_user_extra/model.py"""

import pytest
from unittest.mock import Mock, patch


class TestUserExtra:
    """Test suite for UserExtra model."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock session."""
        with patch('ckanext.hdx_user_extra.model.meta.Session') as mock:
            yield mock

    @pytest.fixture
    def mock_user_extra_table(self):
        """Create a mock user_extra_table."""
        with patch('ckanext.hdx_user_extra.model.user_extra_table') as mock:
            mock.exists = Mock(return_value=True)
            yield mock

    def test_user_extra_init(self) -> None:
        """Test UserExtra initialization."""
        from ckanext.hdx_user_extra.model import UserExtra

        user_extra = UserExtra('user-123', 'test_key', 'test_value')

        assert user_extra.user_id == 'user-123'
        assert user_extra.key == 'test_key'
        assert user_extra.value == 'test_value'

    def test_user_extra_get_found(self, mock_session: Mock) -> None:
        """Test getting existing user extra by user_id and key."""
        from ckanext.hdx_user_extra.model import UserExtra

        # Setup mock
        mock_query = Mock()
        mock_filter = Mock()
        mock_user_extra = UserExtra('user-123', 'test_key', 'test_value')

        mock_session.query.return_value = mock_query
        mock_query.filter_by.return_value = mock_filter
        mock_filter.first.return_value = mock_user_extra

        # Execute
        result = UserExtra.get('user-123', 'test_key')

        # Assertions
        assert result == mock_user_extra
        assert result.user_id == 'user-123'
        assert result.key == 'test_key'
        mock_session.query.assert_called_once_with(UserExtra)
        mock_query.filter_by.assert_called_once_with(user_id='user-123', key='test_key')
        mock_filter.first.assert_called_once()

    def test_user_extra_get_not_found(self, mock_session: Mock) -> None:
        """Test getting non-existent user extra."""
        from ckanext.hdx_user_extra.model import UserExtra

        # Setup mock
        mock_query = Mock()
        mock_filter = Mock()

        mock_session.query.return_value = mock_query
        mock_query.filter_by.return_value = mock_filter
        mock_filter.first.return_value = None

        # Execute
        result = UserExtra.get('user-999', 'nonexistent_key')

        # Assertions
        assert result is None
        mock_query.filter_by.assert_called_once_with(user_id='user-999', key='nonexistent_key')

    def test_user_extra_get_by_user_found(self, mock_session: Mock) -> None:
        """Test getting all extras for a user."""
        from ckanext.hdx_user_extra.model import UserExtra

        # Setup mock
        mock_query = Mock()
        mock_filter = Mock()
        mock_extras = [
            UserExtra('user-123', 'key1', 'value1'),
            UserExtra('user-123', 'key2', 'value2'),
            UserExtra('user-123', 'key3', 'value3'),
        ]

        mock_session.query.return_value = mock_query
        mock_query.filter_by.return_value = mock_filter
        mock_filter.all.return_value = mock_extras

        # Execute
        result = UserExtra.get_by_user('user-123')

        # Assertions
        assert len(result) == 3
        assert all(extra.user_id == 'user-123' for extra in result)
        assert result[0].key == 'key1'
        assert result[1].key == 'key2'
        assert result[2].key == 'key3'
        mock_session.query.assert_called_once_with(UserExtra)
        mock_query.filter_by.assert_called_once_with(user_id='user-123')
        mock_filter.all.assert_called_once()

    def test_user_extra_get_by_user_empty(self, mock_session: Mock) -> None:
        """Test getting extras for user with no extras."""
        from ckanext.hdx_user_extra.model import UserExtra

        # Setup mock
        mock_query = Mock()
        mock_filter = Mock()

        mock_session.query.return_value = mock_query
        mock_query.filter_by.return_value = mock_filter
        mock_filter.all.return_value = []

        # Execute
        result = UserExtra.get_by_user('user-999')

        # Assertions
        assert result == []
        mock_query.filter_by.assert_called_once_with(user_id='user-999')

    def test_user_extra_check_exists(self, mock_user_extra_table: Mock) -> None:
        """Test checking if user_extra table exists."""
        from ckanext.hdx_user_extra.model import UserExtra

        # Execute
        result = UserExtra.check_exists()

        # Assertions
        assert result is True
        mock_user_extra_table.exists.assert_called_once()

    def test_user_extra_check_exists_false(self) -> None:
        """Test checking if user_extra table exists when it doesn't."""
        from ckanext.hdx_user_extra.model import UserExtra

        with patch('ckanext.hdx_user_extra.model.user_extra_table') as mock_table:
            mock_table.exists.return_value = False

            # Execute
            result = UserExtra.check_exists()

            # Assertions
            assert result is False

    def test_user_extra_as_dict(self) -> None:
        """Test converting UserExtra to dictionary."""
        from ckanext.hdx_user_extra.model import UserExtra

        user_extra = UserExtra('user-123', 'test_key', 'test_value')

        # Execute
        result = user_extra.as_dict()

        # Assertions
        assert isinstance(result, dict)
        assert result['user_id'] == 'user-123'
        assert result['key'] == 'test_key'
        assert result['value'] == 'test_value'
        assert not any(k.startswith('_') for k in result.keys())


class TestSetup:
    """Test suite for setup function."""

    @patch('ckanext.hdx_user_extra.model.create_table')
    @patch('ckanext.hdx_user_extra.model.define_user_extra_table')
    @patch('ckanext.hdx_user_extra.model.user_extra_table', None)
    def test_setup_creates_table_definition(self, mock_define: Mock, mock_create: Mock) -> None:
        """Test setup creates table definition when it doesn't exist."""
        from ckanext.hdx_user_extra.model import setup

        # Execute
        setup()

        # Assertions
        mock_define.assert_called_once()
        mock_create.assert_called_once()

    @patch('ckanext.hdx_user_extra.model.create_table')
    @patch('ckanext.hdx_user_extra.model.define_user_extra_table')
    def test_setup_skips_definition_if_exists(self, mock_define: Mock, mock_create: Mock) -> None:
        """Test setup skips table definition if it already exists."""
        from ckanext.hdx_user_extra.model import setup

        with patch('ckanext.hdx_user_extra.model.user_extra_table', Mock()):
            # Execute
            setup()

            # Assertions
            mock_define.assert_not_called()
            mock_create.assert_called_once()


class TestDefineUserExtraTable:
    """Test suite for define_user_extra_table function."""

    @patch('ckanext.hdx_user_extra.model.mapper')
    @patch('ckanext.hdx_user_extra.model.Index')
    @patch('ckanext.hdx_user_extra.model.Table')
    @patch('ckanext.hdx_user_extra.model.meta')
    def test_define_user_extra_table(
        self, mock_meta: Mock, mock_table: Mock, mock_index: Mock, mock_mapper: Mock
    ) -> None:
        """Test defining user_extra table."""
        from ckanext.hdx_user_extra.model import define_user_extra_table

        # Setup mocks
        mock_table_instance = Mock()
        mock_table.return_value = mock_table_instance
        mock_table_instance.c.user_id = 'user_id_column'
        mock_table_instance.c.key = 'key_column'

        # Execute
        define_user_extra_table()

        # Assertions
        mock_table.assert_called_once()
        table_call = mock_table.call_args
        assert table_call[0][0] == 'user_extra'

        # Verify columns are defined
        columns = [arg for arg in table_call[0][2:]]
        assert len(columns) == 4  # id, user_id, key, value

        mock_index.assert_called_once()
        mock_mapper.assert_called_once()


class TestCreateTable:
    """Test suite for create_table function."""

    @patch('ckanext.hdx_user_extra.model.model.ensure_engine')
    @patch('ckanext.hdx_user_extra.model.model.user_table')
    def test_create_table_when_not_exists(self, mock_user_table: Mock, mock_ensure_engine: Mock) -> None:
        """Test creating user_extra table when it doesn't exist."""
        from ckanext.hdx_user_extra.model import create_table

        # Setup mocks
        mock_engine = Mock()
        mock_ensure_engine.return_value = mock_engine
        mock_user_table.exists.return_value = True

        with patch('ckanext.hdx_user_extra.model.user_extra_table') as mock_extra_table:
            mock_extra_table.exists.return_value = False
            mock_extra_table.create = Mock()

            # Execute
            create_table()

            # Assertions
            mock_ensure_engine.assert_called_once()
            mock_user_table.exists.assert_called_once_with(mock_engine)
            mock_extra_table.exists.assert_called_once_with(mock_engine)
            mock_extra_table.create.assert_called_once_with(mock_engine)

    @patch('ckanext.hdx_user_extra.model.model.ensure_engine')
    @patch('ckanext.hdx_user_extra.model.model.user_table')
    def test_create_table_when_already_exists(self, mock_user_table: Mock, mock_ensure_engine: Mock) -> None:
        """Test creating user_extra table when it already exists."""
        from ckanext.hdx_user_extra.model import create_table

        # Setup mocks
        mock_engine = Mock()
        mock_ensure_engine.return_value = mock_engine
        mock_user_table.exists.return_value = True

        with patch('ckanext.hdx_user_extra.model.user_extra_table') as mock_extra_table:
            mock_extra_table.exists.return_value = True
            mock_extra_table.create = Mock()

            # Execute
            create_table()

            # Assertions
            mock_extra_table.create.assert_not_called()

    @patch('ckanext.hdx_user_extra.model.model.ensure_engine')
    @patch('ckanext.hdx_user_extra.model.model.user_table')
    def test_create_table_when_user_table_not_exists(self, mock_user_table: Mock, mock_ensure_engine: Mock) -> None:
        """Test creating user_extra table when user table doesn't exist."""
        from ckanext.hdx_user_extra.model import create_table

        # Setup mocks
        mock_engine = Mock()
        mock_ensure_engine.return_value = mock_engine
        mock_user_table.exists.return_value = False

        with patch('ckanext.hdx_user_extra.model.user_extra_table') as mock_extra_table:
            mock_extra_table.create = Mock()

            # Execute
            create_table()

            # Assertions
            mock_extra_table.create.assert_not_called()


class TestDeleteTable:
    """Test suite for delete_table function."""

    @patch('builtins.print')
    def test_delete_table_when_exists(self, mock_print: Mock) -> None:
        """Test deleting data from user_extra table when it exists."""
        from ckanext.hdx_user_extra.model import delete_table

        with patch('ckanext.hdx_user_extra.model.user_extra_table') as mock_table:
            mock_table.exists.return_value = True
            mock_table.delete = Mock()

            # Execute
            delete_table()

            # Assertions
            mock_table.exists.assert_called_once()
            mock_table.delete.assert_called_once()
            assert mock_print.call_count == 3

    @patch('builtins.print')
    def test_delete_table_when_not_exists(self, mock_print: Mock) -> None:
        """Test deleting data from user_extra table when it doesn't exist."""
        from ckanext.hdx_user_extra.model import delete_table

        with patch('ckanext.hdx_user_extra.model.user_extra_table') as mock_table:
            mock_table.exists.return_value = False
            mock_table.delete = Mock()

            # Execute
            delete_table()

            # Assertions
            mock_table.delete.assert_not_called()
            assert mock_print.call_count == 1


class TestDropTable:
    """Test suite for drop_table function."""

    @patch('builtins.print')
    def test_drop_table_when_exists(self, mock_print: Mock) -> None:
        """Test dropping user_extra table when it exists."""
        from ckanext.hdx_user_extra.model import drop_table

        with patch('ckanext.hdx_user_extra.model.user_extra_table') as mock_table:
            mock_table.exists.return_value = True
            mock_table.drop = Mock()

            # Execute
            drop_table()

            # Assertions
            mock_table.exists.assert_called_once()
            mock_table.drop.assert_called_once()
            assert mock_print.call_count == 3

    @patch('builtins.print')
    def test_drop_table_when_not_exists(self, mock_print: Mock) -> None:
        """Test dropping user_extra table when it doesn't exist."""
        from ckanext.hdx_user_extra.model import drop_table

        with patch('ckanext.hdx_user_extra.model.user_extra_table') as mock_table:
            mock_table.exists.return_value = False
            mock_table.drop = Mock()

            # Execute
            drop_table()

            # Assertions
            mock_table.drop.assert_not_called()
            assert mock_print.call_count == 1
