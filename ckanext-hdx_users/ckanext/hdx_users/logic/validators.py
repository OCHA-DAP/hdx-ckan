import ckan.plugins.toolkit as tk


def user_email_validator(key, data, errors, context):
    '''HDX valiator for emails as identifiers.'''
    model = context['model']
    # Convert email to lowercase
    data[key] = data[key].lower()
    email = data[key]

    from validate_email import validate_email
    if not validate_email(email, check_mx=False, verify=False):
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
        errors[key].append(tk._('That login email is not available.'))

    return
