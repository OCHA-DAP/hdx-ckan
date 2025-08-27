from typing import Any
import re
import regex as regex_mod
from six import string_types

import ckan.plugins.toolkit as tk
from ckan.types import (
    Context, FlattenDataDict, FlattenErrorDict,
    FlattenKey)
from ckanext.hdx_theme.util.mail import hdx_validate_email as validate_email

_ = tk._
Invalid = tk.Invalid

def user_email_validator(key, data, errors, context):
    """HDX validator for emails as identifiers."""
    model = context['model']
    session = context['session']

    # Convert email to lowercase
    data[key] = data[key].lower()
    email = data[key]

    if not validate_email(email):
        raise Invalid(_('Email address is not valid'))

    if not isinstance(email, string_types):
        raise Invalid(_('User names must be strings'))

    # user = model.User.by_email(email)
    users = session.query(model.User) \
        .filter(model.User.email == data[key]) \
        .filter(model.User.state == 'active').all()
    # if there are no active users with this email, it's free
    if not users:
        return

    else:
        for user in users:
            if user:
                # A user with new_user_name already exists in the database.
                user_obj_from_context = context.get('user_obj')
                if user_obj_from_context and user_obj_from_context.id == user.id:
                    # If there's a user_obj in context with the same id as the
                    # user found in the db, then we must be doing a user_update
                    # and not updating the user name, so don't return an error.
                    return
                errors[key].append(_('The email address is already registered on HDX.'))

    return


# def user_name_validator(key, data, errors, context):
#     '''Validate a new user name.
#
#     Copy of the validator with the same name from CKAN core BUT allows for change in username
#
#     :raises ckan.lib.navl.dictization_functions.Invalid: if ``data[key]`` is
#         not a string
#     :rtype: None
#
#     '''
#     model = context['model']
#     new_user_name = data[key]
#
#     if not isinstance(new_user_name, string_types):
#         raise Invalid(_('User names must be strings'))
#
#     user = model.User.get(new_user_name)
#     user_obj_from_context = context.get('user_obj')
#     if user is not None:
#         # A user with new_user_name already exists in the database.
#         if user_obj_from_context and user_obj_from_context.id == user.id:
#             # If there's a user_obj in context with the same id as the user
#             # found in the db, then we must be doing a user_update and not
#             # updating the user name, so don't return an error.
#             return
#         else:
#             # Otherwise return an error: there's already another user with that
#             # name, so you can create a new user with that name or update an
#             # existing user's name to that name.
#             errors[key].append(_(USER_INFO_CONSTANTS['INPUT_USERNAME_ERROR_ALREADY_EXISTS']))

def user_emails_match(key: FlattenKey, data: FlattenDataDict,
                         errors: FlattenErrorDict, context: Context) -> Any:
    """Ensures that email and email confirmation match.
    """
    email = data.get(('email',),None)
    email2 = data.get(('email2',),None)

    if not email == email2:
        errors[key].append(_('The emails you entered do not match'))
    else:
        #Set correct email
        data[('email',)] = email


def hdx_fullname_unicode_validator(key: FlattenKey, data: FlattenDataDict,
                                  errors: FlattenErrorDict, context: Context) -> Any:
    """
    NAVL validator for the 'fullname' field.
    Ensures the value:
      - is not empty
      - is a Unicode string
      - contains:
          * letters (including accented letters from Europe, Nordics, Eastern Europe)
          * digits
          * allowed punctuation: space, hyphen, apostrophe, period
    This validator is easily extendable if new special characters are needed.
    """

    # Get the current value for this field
    value = data.get(key)

    # Check if the value is empty or whitespace-only
    if not value or not value.strip():
        errors[key].append(_('Full name cannot be empty.'))
        return

    # Ensure the value is a Unicode string (like 'ensure_str')
    if not isinstance(value, str):
        try:
            if isinstance(value, bytes):
                value = value.decode('utf-8')
            else:
                raise TypeError # decode bytes to str
        except Exception:
            errors[key].append(_('Full name must be a valid Unicode string.'))
            return

    # Allowed punctuation and special characters
    # Use regex to validate allowed characters: Unicode letters, digits, space, hyphen, apostrophe, period
    pattern = r"^[\p{L}\p{N} \-'._]+$"
    try:
        regex_fullmatch = regex_mod.fullmatch
        regex_pattern = pattern
    except ImportError:
        # Fallback: re does not support \p{L}, so use a best-effort pattern for ASCII/Latin
        regex_fullmatch = re.fullmatch
        regex_pattern = r"^[\w \-'._]+$"

    if not regex_fullmatch(regex_pattern, value):
        errors[key].append(_('Full name contains invalid characters.'))
    # Strip and update the value in data
    data[key] = value.strip()
