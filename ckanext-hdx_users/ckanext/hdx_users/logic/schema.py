'''
Created on July 2nd, 2015

@author: dan
'''
from ckan.lib.navl.validators import (ignore_missing,
                                      keep_extras,
                                      not_empty,
                                      empty,
                                      ignore,
                                      if_empty_same_as,
                                      not_missing,
                                      ignore_empty
                                      )
from ckan.logic.validators import (package_id_not_changed,
                                   package_id_exists,
                                   package_id_or_name_exists,
                                   resource_id_exists,
                                   name_validator,
                                   package_name_validator,
                                   package_version_validator,
                                   group_name_validator,
                                   tag_length_validator,
                                   tag_name_validator,
                                   tag_string_convert,
                                   duplicate_extras_key,
                                   ignore_not_package_admin,
                                   ignore_not_group_admin,
                                   ignore_not_sysadmin,
                                   no_http,
                                   tag_not_uppercase,
                                   user_name_validator,
                                   user_password_validator,
                                   user_both_passwords_entered,
                                   user_passwords_match,
                                   user_password_not_empty,
                                   isodate,
                                   int_validator,
                                   natural_number_validator,
                                   is_positive_integer,
                                   boolean_validator,
                                   user_about_validator,
                                   vocabulary_name_validator,
                                   vocabulary_id_not_changed,
                                   vocabulary_id_exists,
                                   user_id_exists,
                                   user_id_or_name_exists,
                                   object_id_validator,
                                   activity_type_exists,
                                   resource_id_exists,
                                   tag_not_in_vocabulary,
                                   group_id_exists,
                                   owner_org_validator,
                                   user_name_exists,
                                   role_exists,
                                   url_validator,
                                   datasets_with_no_organization_cannot_be_private,
                                   list_of_strings,
                                   if_empty_guess_format,
                                   clean_format,
                                   no_loops_in_hierarchy,
                                   filter_fields_and_values_should_have_same_length,
                                   filter_fields_and_values_exist_and_are_valid,
                                   extra_key_not_in_root_schema,
                                   empty_if_not_sysadmin,
                                   package_id_does_not_exist,
                                   )
from ckan.logic.converters import (convert_user_name_or_id_to_id,
                                   convert_package_name_or_id_to_id,
                                   convert_group_name_or_id_to_id,
                                   convert_to_json_if_string,
                                   convert_to_list_if_string,
                                   remove_whitespace,
                                   extras_unicode_convert,
                                   )
from formencode.validators import OneOf
import ckan.model
import ckan.lib.maintain as maintain

import ckan.plugins.toolkit as tk


def register_user_schema():

    user_email_validator = tk.get_validator('user_email_validator')

    schema = {
        'name': [not_empty, unicode],
        'email': [not_empty, user_email_validator, unicode],
    }
    return schema


def register_details_user_schema():

    user_email_validator = tk.get_validator('user_email_validator')

    schema = {
        'id': [ignore_missing, unicode],
        'name': [not_empty, name_validator, user_name_validator, unicode],
        'fullname': [ignore_missing, unicode],
        'password': [user_password_validator, user_password_not_empty, ignore_missing, unicode],
        'email': [not_empty, user_email_validator, unicode],
        'state': [ignore_missing],
    }
    return schema
