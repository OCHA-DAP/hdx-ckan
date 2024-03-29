from typing import Any

from six import string_types

import ckan.plugins.toolkit as tk
from ckan.types import (
    Context, FlattenDataDict, FlattenErrorDict,
    FlattenKey)
from ckanext.hdx_theme.util.mail import hdx_validate_email as validate_email

_ = tk._
Invalid = tk.Invalid

def user_email_validator(key, data, errors, context):
    '''HDX validator for emails as identifiers.'''
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
