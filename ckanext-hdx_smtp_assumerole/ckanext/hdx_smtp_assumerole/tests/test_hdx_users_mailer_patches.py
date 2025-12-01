# encoding: utf-8

import unittest
from unittest.mock import patch
from email.header import Header

import ckanext.hdx_smtp_assumerole.helpers.hdx_users_mailer_patches as patches_module
from ckanext.hdx_smtp_assumerole.helpers.hdx_users_mailer_patches import (
    _get_decoded_str,
    is_patched,
    patch_hdx_users_mailer,
    unpatch_hdx_users_mailer
)


class TestGetDecodedStr(unittest.TestCase):
    """Tests for _get_decoded_str helper function"""

    def test_decode_simple_string(self):
        """Test decoding a simple ASCII string"""
        result = _get_decoded_str('John Doe')
        self.assertEqual(result, 'John Doe')

    def test_decode_empty_string(self):
        """Test decoding an empty string"""
        result = _get_decoded_str('')
        self.assertEqual(result, '')

    def test_decode_none(self):
        """Test decoding None"""
        result = _get_decoded_str(None)
        self.assertEqual(result, '')

    def test_decode_utf8_string(self):
        """Test decoding a UTF-8 string"""
        result = _get_decoded_str('François Müller')
        self.assertEqual(result, 'François Müller')

    def test_decode_encoded_header(self):
        """Test decoding an encoded email header"""
        # Create an encoded header
        encoded = str(Header('Test User', 'utf-8'))
        result = _get_decoded_str(encoded)
        self.assertIn('Test', result)


class TestPatchFunctions(unittest.TestCase):
    """Tests for patch/unpatch functions"""

    def setUp(self):
        """Reset patching state before each test"""
        # Reset module state
        patches_module._patches_applied = False
        patches_module._original_mail_recipient_html = None

    def test_is_patched_initially_false(self):
        """Test that is_patched returns False initially"""
        self.assertFalse(is_patched())

    def test_patch_hdx_users_mailer_no_module(self):
        """Test patching when hdx_users module is not available"""
        # Mock the import to raise ImportError
        import sys
        original_import = __builtins__.__import__

        def mock_import(name, *args, **kwargs):
            if 'ckanext.hdx_users' in name:
                raise ImportError('No module named ckanext.hdx_users')
            return original_import(name, *args, **kwargs)

        # Reset state to ensure clean test
        patches_module._patches_applied = False

        with patch('builtins.__import__', side_effect=mock_import):
            # This should handle ImportError gracefully
            patch_hdx_users_mailer()
            # Should not raise exception, just log warning
            self.assertFalse(is_patched())

    def test_patch_hdx_users_mailer_idempotent(self):
        """Test that patching multiple times is safe"""
        patches_module._patches_applied = True

        # Second call should return early
        patch_hdx_users_mailer()
        self.assertTrue(is_patched())

    def test_unpatch_when_not_patched(self):
        """Test unpatching when patches are not applied"""
        # Should not raise exception
        unpatch_hdx_users_mailer()
        self.assertFalse(is_patched())

    def test_unpatch_no_module(self):
        """Test unpatching when hdx_users module is not available"""
        patches_module._patches_applied = True

        # Should handle ImportError gracefully
        unpatch_hdx_users_mailer()
