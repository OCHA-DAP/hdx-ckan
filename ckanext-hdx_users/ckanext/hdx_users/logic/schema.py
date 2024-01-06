'''
Created on July 2nd, 2015

@author: dan
'''

import ckan.plugins.toolkit as tk
from ckan.logic.schema import validator_args

unicode_safe = tk.get_validator('unicode_safe')

@validator_args
def register_user_schema(not_empty, user_email_validator):

    schema = {
        'name': [not_empty, unicode_safe],
        'email': [not_empty, user_email_validator, unicode_safe],
    }
    return schema


@validator_args
def register_details_user_schema(ignore_missing, not_empty, name_validator, user_name_validator,
                                 user_password_validator, user_password_not_empty,
                                 user_email_validator):

    schema = {
        'id': [ignore_missing, unicode_safe],
        'name': [not_empty, name_validator, user_name_validator, unicode_safe],
        'fullname': [ignore_missing, unicode_safe],
        'password': [user_password_validator, user_password_not_empty, ignore_missing, unicode_safe],
        'email': [not_empty, user_email_validator, unicode_safe],
        'state': [ignore_missing],
    }
    return schema
