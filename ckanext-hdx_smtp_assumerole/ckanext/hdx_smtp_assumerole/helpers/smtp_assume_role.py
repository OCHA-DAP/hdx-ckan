# encoding: utf-8
"""
Backward-compatibility shim.

All AssumeRole logic has moved to
``ckanext.hdx_theme.helpers.aws_credentials``.
``SMTPAssumeRoleException`` is kept here as an alias so any code
that still catches it continues to work.
"""

from ckanext.hdx_theme.helpers.aws_credentials import AwsAssumeRoleException

# Alias – identical object, so ``except SMTPAssumeRoleException`` catches
# anything raised by the shared credential helpers.
SMTPAssumeRoleException = AwsAssumeRoleException
