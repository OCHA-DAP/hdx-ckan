'''
Created on July 2nd, 2015

@author: dan
'''

import ckan.plugins.toolkit as tk
from ckan.logic.schema import validator_args, user_new_form_schema

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


# @validator_args
# def onboarding_create_user_schema(ignore_missing: Validator, unicode_safe: Validator,
#                                   name_validator: Validator, user_name_validator: Validator,
#                                   user_password_validator: Validator, user_both_passwords_entered: Validator,
#                                   user_passwords_match: Validator,
#                                   ignore_not_sysadmin: Validator,
#                                   not_empty: Validator, strip_value: Validator,
#                                   user_email_validator: Validator, user_about_validator: Validator,
#                                   ignore: Validator, boolean_validator: Validator):
#     return cast(Schema, {
#         'id': [ignore_missing, unicode_safe],
#         'name': [not_empty, name_validator, user_name_validator, unicode_safe],
#         'fullname': [ignore_missing, unicode_safe],
#         'password1': [unicode_safe, user_both_passwords_entered, user_password_validator, user_passwords_match],
#         'password2': [unicode_safe],
#         'password_hash': [ignore_missing, ignore_not_sysadmin, unicode_safe],
#         'email': [not_empty, strip_value, user_email_validator, unicode_safe],
#         # 'about': [ignore_missing, user_about_validator, unicode_safe],
#         'created': [ignore],
#         'sysadmin': [ignore_missing, ignore_not_sysadmin],
#         'reset_key': [ignore],
#         'activity_streams_email_notifications': [ignore_missing,
#                                                  boolean_validator],
#         'state': [ignore_missing],
#     })


@validator_args
def onboarding_user_new_form_schema(unicode_safe, not_empty, strip_value, user_email_validator, ignore_missing,
                                    user_emails_match):
    schema = user_new_form_schema()
    schema['fullname'] = [strip_value, not_empty, unicode_safe]
    schema['email'] = [not_empty, strip_value, user_email_validator, user_emails_match, unicode_safe]
    schema['email2'] = [unicode_safe]
    schema['state'] = [ignore_missing]

    return schema
