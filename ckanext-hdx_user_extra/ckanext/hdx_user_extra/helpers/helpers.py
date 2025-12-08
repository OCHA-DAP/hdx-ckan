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

    Args:
        key (str): The key of the extra field to retrieve.
        user_id (str): The CKAN user id to query.

    Returns:
        Optional[str]: The value associated with `key` for `user_id`, or
        `None` if the extra does not exist.

    Raises:
        None: Any NotFound from the action is handled and results in `None`.

    Notes:
        - Uses CKAN's `user_extra_value_by_key_show` action with a context that
          sets `ignore_auth` to True.
        - This helper is read-only and does not modify the database.
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

    Args:
        user_id (str): The CKAN user id to check.

    Returns:
        bool: True if the `ONBOARDING_USER_EMAIL_UPDATED_KEY` extra exists and
        equals the string `'true'`, otherwise False.

    Example:
        >>> is_user_extra_email_updated('1234')
        False

    Notes:
        - The function relies on `user_extra_value_by_key` and expects the stored
          flag to be the literal string `'true'`.
    """
    is_updated = user_extra_value_by_key(key=ONBOARDING_USER_EMAIL_UPDATED_KEY, user_id=user_id)
    if is_updated:
        return is_updated == 'true'
    return False
