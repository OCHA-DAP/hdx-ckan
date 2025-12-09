import ckan.plugins.toolkit as tk
import ckan.model as model
from ckan.types import Context

from ckanext.hdx_users.helpers.constants import (
    ONBOARDING_USER_EMAIL_UPDATED_KEY,
)

get_action = tk.get_action
NotFound = tk.ObjectNotFound

def user_extra_value_by_key(key: str, user_id: str):
    """
    Retrieve a user's extra value by key.

    This function queries the CKAN database to retrieve a user's extra field value
    associated with a specific key. It uses CKAN's action layer with elevated
    privileges (ignore_auth) for internal operations.

    :param key: The key of the extra field to retrieve.
    :type key: str
    :param user_id: The CKAN user id to query.
    :type user_id: str

    :returns: The value associated with the key for the user, or None if not found.
    :rtype: str or None

    :raises: None - Any NotFound exception is caught and handled internally.
    """
    context: Context = {'session': model.Session, 'model': model, 'ignore_auth': True}
    ue_data_dict = {
        'user_id': user_id,
        'key': key
    }
    try:
        ue_extra = get_action('user_extra_value_by_key_show')(context, ue_data_dict)
    except NotFound:
        return None
    return ue_extra.get(key)

def is_user_extra_email_updated(user_id: str):
    """
    Determine whether the onboarding email for a user was marked as updated.

    This function checks if a specific user extra flag (ONBOARDING_USER_EMAIL_UPDATED_KEY)
    exists and has been set to the string value 'true'. It's used to track whether
    a user has updated their email during the onboarding process.

    :param user_id: The CKAN user id to check.
    :type user_id: str

    :returns: True if the onboarding email flag is set to 'true', False otherwise.
    :rtype: bool
    """
    return user_extra_value_by_key(key=ONBOARDING_USER_EMAIL_UPDATED_KEY, user_id=user_id) == 'true'
