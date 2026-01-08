"""
Tests for YTP Request Util Module.

This module contains unit tests for utility functions used in handling
membership requests in CKAN organizations.
"""

from ckanext.ytp.request.util import (
    _SUBJECT_MEMBERSHIP_REQUEST,
    _MESSAGE_MEMBERSHIP_REQUEST,
    _SUBJECT_MEMBERSHIP_APPROVED,
    _MESSAGE_MEMBERSHIP_APPROVED,
    _SUBJECT_MEMBERSHIP_REJECTED,
    _MESSAGE_MEMBERSHIP_REJECTED,
)


class TestYTPRequestUtil:
    """Test suite for YTP Request utility functions and constants."""

    def test_subject_membership_request_constant(self) -> None:
        """
        Test the membership request email subject constant.
        """
        assert _SUBJECT_MEMBERSHIP_REQUEST == '{user_fullname} sent a request to join your organisation on HDX'
        assert '{user_fullname}' in _SUBJECT_MEMBERSHIP_REQUEST

    def test_message_membership_request_constant(self) -> None:
        """
        Test the membership request email message template constant.
        """
        assert '{org_title}' in _MESSAGE_MEMBERSHIP_REQUEST
        assert '{user_fullname}' in _MESSAGE_MEMBERSHIP_REQUEST
        assert '{user_email}' in _MESSAGE_MEMBERSHIP_REQUEST
        assert '{user_message}' in _MESSAGE_MEMBERSHIP_REQUEST
        assert '{org_add_member_url}' in _MESSAGE_MEMBERSHIP_REQUEST
        assert 'Admin' in _MESSAGE_MEMBERSHIP_REQUEST
        assert 'Editor' in _MESSAGE_MEMBERSHIP_REQUEST
        assert 'Member' in _MESSAGE_MEMBERSHIP_REQUEST
        assert 'hdx@un.org' in _MESSAGE_MEMBERSHIP_REQUEST

    def test_subject_membership_approved_constant(self) -> None:
        """
        Test the membership approved email subject constant.
        """
        assert _SUBJECT_MEMBERSHIP_APPROVED == 'Organisation membership request on HDX has been approved'

    def test_message_membership_approved_constant(self) -> None:
        """
        Test the membership approved email message template constant.
        """
        assert '{organization}' in _MESSAGE_MEMBERSHIP_APPROVED
        assert '{role}' in _MESSAGE_MEMBERSHIP_APPROVED
        assert 'approved' in _MESSAGE_MEMBERSHIP_APPROVED
        assert 'the HDX Team' in _MESSAGE_MEMBERSHIP_APPROVED

    def test_subject_membership_rejected_constant(self) -> None:
        """
        Test the membership rejected email subject constant.
        """
        assert _SUBJECT_MEMBERSHIP_REJECTED == 'Organisation membership request on HDX has been rejected'

    def test_message_membership_rejected_constant(self) -> None:
        """
        Test the membership rejected email message template constant.
        """
        assert '{organization}' in _MESSAGE_MEMBERSHIP_REJECTED
        assert '{role}' in _MESSAGE_MEMBERSHIP_REJECTED
        assert 'rejected' in _MESSAGE_MEMBERSHIP_REJECTED
        assert 'the HDX Team' in _MESSAGE_MEMBERSHIP_REJECTED

    def test_membership_request_subject_formatting(self) -> None:
        """
        Test formatting the membership request subject with actual values.
        """
        user_fullname = 'John Doe'
        formatted = _SUBJECT_MEMBERSHIP_REQUEST.format(user_fullname=user_fullname)

        assert user_fullname in formatted
        assert 'sent a request to join your organisation on HDX' in formatted

    def test_membership_request_message_formatting(self) -> None:
        """
        Test formatting the membership request message with actual values.
        """
        data = {
            'org_title': 'Test Organization',
            'user_fullname': 'John Doe',
            'user_email': 'john.doe@example.com',
            'user_message': 'I would like to join your organization',
            'org_add_member_url': 'https://example.com/org/test-org/members',
        }

        formatted = _MESSAGE_MEMBERSHIP_REQUEST.format(**data)

        assert data['org_title'] in formatted
        assert data['user_fullname'] in formatted
        assert data['user_email'] in formatted
        assert data['user_message'] in formatted
        assert data['org_add_member_url'] in formatted
        assert 'Dear Admin' in formatted
        assert 'private datasets' in formatted

    def test_membership_approved_subject_is_static(self) -> None:
        """
        Test that the approved subject requires no formatting.
        """
        # Should not raise any formatting errors
        formatted = _SUBJECT_MEMBERSHIP_APPROVED.format()
        assert formatted == _SUBJECT_MEMBERSHIP_APPROVED

    def test_membership_approved_message_formatting(self) -> None:
        """
        Test formatting the membership approved message with actual values.
        """
        data = {'organization': 'Test Organization', 'role': 'Editor'}

        formatted = _MESSAGE_MEMBERSHIP_APPROVED.format(**data)

        assert data['organization'] in formatted
        assert data['role'] in formatted
        assert 'approved' in formatted

    def test_membership_rejected_subject_is_static(self) -> None:
        """
        Test that the rejected subject requires no formatting.
        """
        # Should not raise any formatting errors
        formatted = _SUBJECT_MEMBERSHIP_REJECTED.format()
        assert formatted == _SUBJECT_MEMBERSHIP_REJECTED

    def test_membership_rejected_message_formatting(self) -> None:
        """
        Test formatting the membership rejected message with actual values.
        """
        data = {'organization': 'Test Organization', 'role': 'Member'}

        formatted = _MESSAGE_MEMBERSHIP_REJECTED.format(**data)

        assert data['organization'] in formatted
        assert data['role'] in formatted
        assert 'rejected' in formatted

    def test_all_messages_contain_hdx_team_signature(self) -> None:
        """
        Test that all email message templates contain the HDX Team signature.
        """
        assert 'the HDX Team' in _MESSAGE_MEMBERSHIP_REQUEST
        assert 'the HDX Team' in _MESSAGE_MEMBERSHIP_APPROVED
        assert 'the HDX Team' in _MESSAGE_MEMBERSHIP_REJECTED

    def test_membership_request_contains_role_descriptions(self) -> None:
        """
        Test that the membership request message contains role descriptions.
        """
        assert 'Admin:' in _MESSAGE_MEMBERSHIP_REQUEST
        assert 'Editor:' in _MESSAGE_MEMBERSHIP_REQUEST
        assert 'Member:' in _MESSAGE_MEMBERSHIP_REQUEST
        assert 'add, edit and delete datasets' in _MESSAGE_MEMBERSHIP_REQUEST
        assert 'manage organisation membership' in _MESSAGE_MEMBERSHIP_REQUEST

    def test_membership_request_contains_security_warning(self) -> None:
        """
        Test that the membership request message contains security warnings.
        """
        assert 'private datasets' in _MESSAGE_MEMBERSHIP_REQUEST
        assert 'trusted network' in _MESSAGE_MEMBERSHIP_REQUEST
        assert 'verify who the user is' in _MESSAGE_MEMBERSHIP_REQUEST

    def test_membership_request_contains_contact_information(self) -> None:
        """
        Test that the membership request message contains contact information.
        """
        assert 'hdx@un.org' in _MESSAGE_MEMBERSHIP_REQUEST
        assert 'mailto:hdx@un.org' in _MESSAGE_MEMBERSHIP_REQUEST

    def test_membership_request_contains_documentation_link(self) -> None:
        """
        Test that the membership request message contains documentation link.
        """
        assert 'gdoc.pub/doc' in _MESSAGE_MEMBERSHIP_REQUEST
        assert 'how to manage organisational members' in _MESSAGE_MEMBERSHIP_REQUEST

    def test_all_messages_use_html_formatting(self) -> None:
        """
        Test that all email message templates use HTML formatting.
        """
        assert '<br/>' in _MESSAGE_MEMBERSHIP_REQUEST
        assert '<br/>' in _MESSAGE_MEMBERSHIP_APPROVED
        assert '<br/>' in _MESSAGE_MEMBERSHIP_REJECTED

    def test_membership_request_message_formatting_with_special_characters(self) -> None:
        """
        Test formatting the membership request message with special characters.
        """
        data = {
            'org_title': 'Test & Organization <script>',
            'user_fullname': "John O'Doe",
            'user_email': 'john.doe+test@example.com',
            'user_message': 'I would like to join & contribute',
            'org_add_member_url': 'https://example.com/org/test-org/members?ref=email&action=approve',
        }

        # Should not raise any formatting errors
        formatted = _MESSAGE_MEMBERSHIP_REQUEST.format(**data)

        assert data['org_title'] in formatted
        assert data['user_fullname'] in formatted
        assert data['user_email'] in formatted

    def test_membership_approved_message_with_different_roles(self) -> None:
        """
        Test approved message formatting with different role values.
        """
        roles = ['Admin', 'Editor', 'Member']

        for role in roles:
            data = {'organization': 'Test Organization', 'role': role}
            formatted = _MESSAGE_MEMBERSHIP_APPROVED.format(**data)
            assert role in formatted

    def test_membership_rejected_message_with_different_roles(self) -> None:
        """
        Test rejected message formatting with different role values.
        """
        roles = ['Admin', 'Editor', 'Member']

        for role in roles:
            data = {'organization': 'Test Organization', 'role': role}
            formatted = _MESSAGE_MEMBERSHIP_REJECTED.format(**data)
            assert role in formatted
