'''
Created on July 2nd, 2015

@author: dan
'''

from ckan.logic.schema import validator_args

@validator_args
def register_user_schema(not_empty, user_email_validator):

    schema = {
        'name': [not_empty, unicode],
        'email': [not_empty, user_email_validator, unicode],
    }
    return schema


@validator_args
def register_details_user_schema(ignore_missing, not_empty, name_validator, user_name_validator,
                                 user_password_validator, user_password_not_empty,
                                 user_email_validator):

    schema = {
        'id': [ignore_missing, unicode],
        'name': [not_empty, name_validator, user_name_validator, unicode],
        'fullname': [ignore_missing, unicode],
        'password': [user_password_validator, user_password_not_empty, ignore_missing, unicode],
        'email': [not_empty, user_email_validator, unicode],
        'state': [ignore_missing],
    }
    return schema
