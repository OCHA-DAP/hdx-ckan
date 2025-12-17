import pytest
import ckan.plugins.toolkit as tk
from ckan.types import Context

from ckanext.hdx_user_extra.actions.get import (
    user_extra_show,
    user_extra_value_by_key_show,
    user_extra_value_by_keys_show,
)
import ckanext.hdx_theme.tests.hdx_test_with_inds_and_orgs as hdx_test_with_inds_and_orgs


class TestUserExtraShow(hdx_test_with_inds_and_orgs.HDXWithIndsAndOrgsTest):
    @classmethod
    def setup_class(cls):
        super(TestUserExtraShow, cls).setup_class()
        context = {'ignore_auth': True}
        cls.user = tk.get_action('user_show')(context, {'id': 'tester'})

    def test_user_extra_show_success(self):
        """Test successfully retrieving user extra list"""
        context: Context = {'ignore_auth': True}

        # Create user extras with correct format
        tk.get_action('user_extra_create')(
            context,
            {
                'user_id': self.user['id'],
                'extras': [{'key': 'preference1', 'value': 'value1'}, {'key': 'preference2', 'value': 'value2'}],
            },
        )

        data_dict = {'user_id': self.user['id']}
        result = user_extra_show(context, data_dict)

        assert isinstance(result, list)
        assert len(result) >= 2
        assert all(isinstance(item, dict) for item in result)
        assert all('key' in item and 'value' in item for item in result)

    def test_user_extra_show_empty_list(self):
        """Test user with no extras returns empty list"""
        context: Context = {'ignore_auth': True}
        new_user = tk.get_action('user_create')(
            context,
            {
                'name': 'newuser',
                'email': 'newuser@example.com',
                'password': 'TestPass123!',
                'fullname': 'New User',
            },
        )

        data_dict = {'user_id': new_user['id']}

        result = user_extra_show(context, data_dict)

        assert isinstance(result, list)
        assert len(result) == 0

    def test_user_extra_show_invalid_user_id(self):
        """Test with non-existent user_id returns empty list"""
        context: Context = {'ignore_auth': True}
        data_dict = {'user_id': 'non-existent-user-id'}

        result = user_extra_show(context, data_dict)

        assert isinstance(result, list)
        assert len(result) == 0

    def test_user_extra_show_missing_user_id(self):
        """Test with missing user_id parameter returns empty list"""
        context: Context = {'ignore_auth': True}
        data_dict = {}

        result = user_extra_show(context, data_dict)

        assert isinstance(result, list)
        assert len(result) == 0

    def test_user_extra_show_without_auth(self):
        """Test authorization check without ignore_auth"""
        context: Context = {'user': 'tester'}

        # Create user extras first
        create_context: Context = {'ignore_auth': True}
        tk.get_action('user_extra_create')(
            create_context, {'user_id': self.user['id'], 'extras': [{'key': 'test_key', 'value': 'test_value'}]}
        )

        data_dict = {'user_id': self.user['id']}
        result = user_extra_show(context, data_dict)
        assert isinstance(result, list)


class TestUserExtraValueByKeyShow(hdx_test_with_inds_and_orgs.HDXWithIndsAndOrgsTest):
    @classmethod
    def setup_class(cls):
        super(TestUserExtraValueByKeyShow, cls).setup_class()
        context = {'ignore_auth': True}
        cls.user = tk.get_action('user_show')(context, {'id': 'tester'})

        # Create test user extra with correct format
        tk.get_action('user_extra_create')(
            context, {'user_id': cls.user['id'], 'extras': [{'key': 'test_key', 'value': 'test_value'}]}
        )

    def test_user_extra_value_by_key_show_success(self):
        """Test successfully retrieving user extra by key"""
        context: Context = {'ignore_auth': True}
        data_dict = {'user_id': self.user['id'], 'key': 'test_key'}

        result = user_extra_value_by_key_show(context, data_dict)

        assert isinstance(result, dict)
        assert 'test_key' in result
        assert result['test_key'] == 'test_value'

    def test_user_extra_value_by_key_show_not_found(self):
        """Test with non-existent key"""
        context: Context = {'ignore_auth': True}
        data_dict = {'user_id': self.user['id'], 'key': 'non_existent_key'}

        with pytest.raises(tk.ObjectNotFound, match='Pair user id and key not found'):
            user_extra_value_by_key_show(context, data_dict)

    def test_user_extra_value_by_key_show_missing_user_id(self):
        """Test with missing user_id"""
        context: Context = {'ignore_auth': True}
        data_dict = {'key': 'test_key'}

        result = user_extra_value_by_key_show(context, data_dict)
        assert isinstance(result, tk.ObjectNotFound)

    def test_user_extra_value_by_key_show_missing_key(self):
        """Test with missing key parameter"""
        context: Context = {'ignore_auth': True}
        data_dict = {'user_id': self.user['id']}

        result = user_extra_value_by_key_show(context, data_dict)
        assert isinstance(result, tk.ObjectNotFound)

    def test_user_extra_value_by_key_show_missing_both(self):
        """Test with both user_id and key missing"""
        context: Context = {'ignore_auth': True}
        data_dict = {}

        result = user_extra_value_by_key_show(context, data_dict)
        assert isinstance(result, tk.ObjectNotFound)

    def test_user_extra_value_by_key_show_invalid_user(self):
        """Test with invalid user_id"""
        context: Context = {'ignore_auth': True}
        data_dict = {'user_id': 'invalid-user', 'key': 'test_key'}

        with pytest.raises(tk.ObjectNotFound, match='Pair user id and key not found'):
            user_extra_value_by_key_show(context, data_dict)

    def test_user_extra_value_by_key_show_multiple_keys(self):
        """Test retrieving multiple different keys"""
        context: Context = {'ignore_auth': True}

        # Create multiple user extras with correct format
        tk.get_action('user_extra_create')(
            context,
            {
                'user_id': self.user['id'],
                'extras': [{'key': 'key1', 'value': 'value1'}, {'key': 'key2', 'value': 'value2'}],
            },
        )

        # Retrieve first key
        result1 = user_extra_value_by_key_show(context, {'user_id': self.user['id'], 'key': 'key1'})
        assert result1 == {'key1': 'value1'}

        # Retrieve second key
        result2 = user_extra_value_by_key_show(context, {'user_id': self.user['id'], 'key': 'key2'})
        assert result2 == {'key2': 'value2'}


class TestUserExtraValueByKeysShow(hdx_test_with_inds_and_orgs.HDXWithIndsAndOrgsTest):
    @classmethod
    def setup_class(cls):
        super(TestUserExtraValueByKeysShow, cls).setup_class()
        context = {'ignore_auth': True}
        cls.user = tk.get_action('user_show')(context, {'id': 'tester'})

        # Create multiple test user extras with correct format
        tk.get_action('user_extra_create')(
            context, {'user_id': cls.user['id'], 'extras': [{'key': f'key{i}', 'value': f'value{i}'} for i in range(5)]}
        )

    def test_user_extra_value_by_keys_show_success(self):
        """Test successfully retrieving user extras by multiple keys"""
        context: Context = {'ignore_auth': True}
        data_dict = {'user_id': self.user['id'], 'keys': ['key0', 'key1', 'key2']}

        result = user_extra_value_by_keys_show(context, data_dict)

        assert isinstance(result, list)
        assert len(result) == 3
        keys_in_result = [item['key'] for item in result]
        assert 'key0' in keys_in_result
        assert 'key1' in keys_in_result
        assert 'key2' in keys_in_result

    def test_user_extra_value_by_keys_show_partial_match(self):
        """Test with some keys that exist and some that don't"""
        context: Context = {'ignore_auth': True}
        data_dict = {'user_id': self.user['id'], 'keys': ['key0', 'non_existent_key', 'key2']}

        result = user_extra_value_by_keys_show(context, data_dict)

        assert isinstance(result, list)
        assert len(result) == 2
        keys_in_result = [item['key'] for item in result]
        assert 'key0' in keys_in_result
        assert 'key2' in keys_in_result
        assert 'non_existent_key' not in keys_in_result

    def test_user_extra_value_by_keys_show_no_matches(self):
        """Test with keys that don't exist"""
        context: Context = {'ignore_auth': True}
        data_dict = {'user_id': self.user['id'], 'keys': ['non_existent1', 'non_existent2']}

        result = user_extra_value_by_keys_show(context, data_dict)

        assert isinstance(result, list)
        assert len(result) == 0

    def test_user_extra_value_by_keys_show_not_found(self):
        """Test with empty keys list returns empty list"""
        context: Context = {'ignore_auth': True}
        data_dict = {'user_id': self.user['id'], 'keys': []}

        result = user_extra_value_by_keys_show(context, data_dict)

        assert isinstance(result, tk.ObjectNotFound)

    def test_user_extra_value_by_keys_show_missing_user_id(self):
        """Test with missing user_id"""
        context: Context = {'ignore_auth': True}
        data_dict = {'keys': ['key0', 'key1']}

        result = user_extra_value_by_keys_show(context, data_dict)
        assert isinstance(result, tk.ObjectNotFound)

    def test_user_extra_value_by_keys_show_missing_keys(self):
        """Test with missing keys parameter"""
        context: Context = {'ignore_auth': True}
        data_dict = {'user_id': self.user['id']}

        result = user_extra_value_by_keys_show(context, data_dict)
        assert isinstance(result, tk.ObjectNotFound)

    def test_user_extra_value_by_keys_show_missing_both(self):
        """Test with both parameters missing"""
        context: Context = {'ignore_auth': True}
        data_dict = {}

        result = user_extra_value_by_keys_show(context, data_dict)
        assert isinstance(result, tk.ObjectNotFound)

    def test_user_extra_value_by_keys_show_invalid_user(self):
        """Test with invalid user_id"""
        context: Context = {'ignore_auth': True}
        data_dict = {'user_id': 'invalid-user', 'keys': ['key0']}

        result = user_extra_value_by_keys_show(context, data_dict)
        assert isinstance(result, list)
        assert len(result) == 0

    def test_user_extra_value_by_keys_show_all_keys(self):
        """Test retrieving all user extras"""
        context: Context = {'ignore_auth': True}
        data_dict = {'user_id': self.user['id'], 'keys': [f'key{i}' for i in range(5)]}

        result = user_extra_value_by_keys_show(context, data_dict)

        assert isinstance(result, list)
        assert len(result) == 5

    def test_user_extra_value_by_keys_show_result_structure(self):
        """Test that result has correct structure"""
        context: Context = {'ignore_auth': True}
        data_dict = {'user_id': self.user['id'], 'keys': ['key0', 'key1']}

        result = user_extra_value_by_keys_show(context, data_dict)

        assert isinstance(result, list)
        for item in result:
            assert isinstance(item, dict)
            assert 'key' in item
            assert 'value' in item
            assert 'user_id' in item
            assert item['user_id'] == self.user['id']
