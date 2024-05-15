import logging

import ckan.lib.navl.dictization_functions as dictization_functions
import ckan.logic as logic
import ckan.plugins.toolkit as tk
from ckan.types import Context
from ckan.logic.schema import validator_args
from ckan.lib.navl.dictization_functions import validate

get_action = tk.get_action
check_access = tk.check_access
config = tk.config
h = tk.h
NotAuthorized = tk.NotAuthorized
unicode_safe = tk.get_validator('unicode_safe')
log = logging.getLogger(__name__)


@validator_args
def request_new_organization_schema(not_empty, ignore_missing, hdx_url_validator):
    schema = {
        'name': [not_empty, unicode_safe],
        'description': [not_empty, unicode_safe],
        'website': [ignore_missing, unicode_safe, hdx_url_validator],
        'role': [not_empty, unicode_safe],
        'data_type': [not_empty, unicode_safe],
        'data_already_available': [not_empty, unicode_safe],
        'data_already_available_link': [ignore_missing, unicode_safe, hdx_url_validator],
    }
    return schema


class OrgRequestLogic(object):
    def __init__(self, context: Context, request):
        self.request = request
        self.context = context
        self.form = request.form
        self.schema = request_new_organization_schema()

    def read(self):
        data_dict = logic.clean_dict(
            dictization_functions.unflatten(
                logic.tuplize_dict(logic.parse_params(self.form))))
        return data_dict

    def validate(self, data_dict):
        try:
            validated_response = validate(data_dict, self.schema, self.context)
        except Exception as ex:
            log.error(ex)
        return validated_response
