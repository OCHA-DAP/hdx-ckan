import logging

import ckan.lib.navl.dictization_functions as dictization_functions
import ckan.logic as logic
import ckan.plugins.toolkit as tk
from ckan.types import Context, DataDict, Request, Validator
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
def dataset_contact_contributor_schema(not_empty: Validator, email_validator: Validator):
    schema = {
        'topic': [not_empty, unicode_safe],
        'fullname': [not_empty, unicode_safe],
        'email': [not_empty, email_validator, unicode_safe],
        'msg': [not_empty, unicode_safe],
    }
    return schema


class DatasetContactContributorLogic(object):
    def __init__(self, context: Context, request: Request):
        self.request = request
        self.context = context
        self.form = request.form
        self.schema = dataset_contact_contributor_schema()

    def read(self) -> DataDict:
        data_dict = logic.clean_dict(dictization_functions.unflatten(logic.tuplize_dict(logic.parse_params(self.form))))
        return data_dict

    def validate(self, data_dict: DataDict):
        try:
            validated_response = validate(data_dict, self.schema, self.context)
        except Exception as ex:
            log.error(ex)

        return validated_response

    def send_mail(self):
        data_dict = {
            'topic': self.request.form.get('topic'),
            'fullname': self.request.form.get('fullname'),
            'email': self.request.form.get('email'),
            'msg': self.request.form.get('msg'),
            'pkg_owner_org': self.request.form.get('pkg_owner_org'),
            'pkg_title': self.request.form.get('pkg_title'),
            'pkg_id': self.request.form.get('pkg_id'),
            'pkg_url': h.url_for('dataset_read', id=self.request.form.get('pkg_id'), qualified=True),
            'hdx_email': config.get('hdx.faqrequest.email'),
        }

        get_action('hdx_send_mail_contributor')(self.context, data_dict)
