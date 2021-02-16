from six import string_types
from ckanext.hdx_theme.util.mail import hdx_validate_email as validate_email
import ckan.plugins.toolkit as tk


def user_email_validator(key, data, errors, context):
    '''HDX validator for emails as identifiers.'''
    model = context['model']
    # Convert email to lowercase
    data[key] = data[key].lower()
    email = data[key]

    if not validate_email(email):
        raise tk.Invalid(tk._('Email address is not valid'))

    if not isinstance(email, basestring):
        raise tk.Invalid(tk._('User names must be strings'))

    users = model.User.by_email(email)
    if users:
        # A user with new_user_name already exists in the database.
        user_obj_from_context = context.get('user_obj')
        for user in users:
            if user_obj_from_context and user_obj_from_context.id == user.id:
                # If there's a user_obj in context with the same id as the
                # user found in the db, then we must be doing a user_update
                # and not updating the user name, so don't return an error.
                return
        errors[key].append(tk._('The email address is already registered on HDX. Please use the sign in screen below.'))

    return


def user_name_validator(key, data, errors, context):
    '''Validate a new user name.

    Copy of the validator with the same name from CKAN core BUT allows for change in username

    :raises ckan.lib.navl.dictization_functions.Invalid: if ``data[key]`` is
        not a string
    :rtype: None

    '''
    model = context['model']
    new_user_name = data[key]

    if not isinstance(new_user_name, string_types):
        raise tk.Invalid(tk._('User names must be strings'))

    user = model.User.get(new_user_name)
    user_obj_from_context = context.get('user_obj')
    if user is not None:
        # A user with new_user_name already exists in the database.
        if user_obj_from_context and user_obj_from_context.id == user.id:
            # If there's a user_obj in context with the same id as the user
            # found in the db, then we must be doing a user_update and not
            # updating the user name, so don't return an error.
            return
        else:
            # Otherwise return an error: there's already another user with that
            # name, so you can create a new user with that name or update an
            # existing user's name to that name.
            errors[key].append(tk._('That login name is not available.'))

