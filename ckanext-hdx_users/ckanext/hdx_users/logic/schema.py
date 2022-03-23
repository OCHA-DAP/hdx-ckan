'''
Created on July 2nd, 2015

@author: dan
'''

from six import text_type

from ckan.logic.schema import validator_args


@validator_args
def register_user_schema(not_empty, user_email_validator):

    schema = {
        'name': [not_empty, text_type],
        'email': [not_empty, user_email_validator, text_type],
    }
    return schema


@validator_args
def register_details_user_schema(ignore_missing, not_empty, name_validator, user_name_validator,
                                 user_password_validator, user_password_not_empty,
                                 user_email_validator):

    schema = {
        'id': [ignore_missing, text_type],
        'name': [not_empty, name_validator, user_name_validator, text_type],
        'fullname': [ignore_missing, text_type],
        'password': [user_password_validator, user_password_not_empty, ignore_missing, text_type],
        'email': [not_empty, user_email_validator, text_type],
        'state': [ignore_missing],
    }
    return schema
