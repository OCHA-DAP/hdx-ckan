import logging

from six import string_types

import ckan.model as model
import ckan.plugins.toolkit as tk

import ckanext.hdx_package.helpers.custom_validator as vd

from ckanext.hdx_package.exceptions import WrongResourceParamName

log = logging.getLogger(__name__)

_get_action = tk.get_action
NotFound = tk.ObjectNotFound


class ContributeFlowWriteLogic(object):
    def __init__(self, dataset_dict):
        self.dataset_dict = dataset_dict

    def process_all(self, user):
        context = {
            'model': model, 'session': model.Session,
            'user': user,
        }
        self.process_tag_string()
        self.process_locations()
        self.process_dataset_date()
        self.process_expected_update_frequency()
        self.process_methodology()
        self.process_maintainer(context)
        self.process_dataset_preview_save()
        self.process_resource_grouping_save()

        self.process_private_and_req_data()

    def process_tag_string(self):
        if self.dataset_dict and not self.dataset_dict.get('tag_string'):
            self.dataset_dict['tag_string'] = ''
            self.dataset_dict['tags'] = []

    def process_locations(self):
        locations = self.dataset_dict.get("locations")
        if locations:
            locations = [locations] if isinstance(locations, string_types) else locations
            groups = []
            for item in locations:
                groups.append({'name': item})
            self.dataset_dict['groups'] = groups
        else:
            self.dataset_dict['groups'] = []

    def process_resources(self):
        '''
        :return: new modified dict containing the resources in the correct format for validating
        :rtype: dict
        '''
        resources_dict = {}
        new_data_dict = {}
        for key, value in self.dataset_dict.items():
            if key.startswith('resources_'):
                key_parts = key.split('__')
                if len(key_parts) == 3:  # 'resources', key, resource number
                    index = int(key_parts[2])
                    resource_dict = resources_dict.get(index, {})
                    resources_dict[index] = resources_dict
                    resource_dict[key_parts] = value
                else:
                    raise WrongResourceParamName('Key {} should have 3 parts'.format(key))

            else:
                new_data_dict[key] = value

        if resources_dict:
            new_data_dict['resources'] = [v for k, v in sorted(resources_dict.items(), key=lambda x: x[0])]

        return new_data_dict

    def process_dataset_date(self):
        # if 'dataset_date' in data_dict:
        #     # date_range1 = data_dict.get('dataset_date')
        #     data_dict['dataset_date'] = '[{date_range1} TO {date_range1}]'.format(date_range1=date_range1)
        if 'date_range1' in self.dataset_dict or 'date_range2' in self.dataset_dict:
            self.dataset_dict['dataset_date'] = '[{date_range1} TO {date_range2}]'.format(
                date_range1=self.dataset_dict.get('date_range1', '*'),
                date_range2=self.dataset_dict.get('date_range2', '*'))

    def process_expected_update_frequency(self):
        if self.dataset_dict.get('data_update_frequency', '-999') == '-999':
            self.dataset_dict['data_update_frequency'] = None

    def process_methodology(self):
        if 'methodology' in self.dataset_dict and self.dataset_dict.get('methodology', '-1') == '-1':
            self.dataset_dict['methodology'] = None

    def process_maintainer(self, context):
        if 'maintainer' in self.dataset_dict:
            # maintainer_dict = logic.get_action('user_show')(context, {'id': data_dict.get('maintainer', 'hdx')})
            # data_dict['maintainer'] = maintainer_dict.get('id', None)
            # data_dict['maintainer_email'] = maintainer_dict.get('email', None)
            try:
                maintainer_dict = _get_action('user_show')(context, {'id': self.dataset_dict.get('maintainer', 'hdx')})
                if maintainer_dict:
                    self.dataset_dict['maintainer'] = maintainer_dict.get('id', None)
                    self.dataset_dict['maintainer_email'] = maintainer_dict.get('email', None)
            except NotFound as e:
                log.info("Maintainer or user not found!")

    def process_dataset_preview_save(self):
        if 'dataset_preview_check' in self.dataset_dict:
            if self.dataset_dict.get('dataset_preview_check', '1') == '1':
                if 'dataset_preview_value' in self.dataset_dict \
                        and self.dataset_dict.get('dataset_preview_value') == vd._DATASET_PREVIEW_FIRST_RESOURCE:

                    self.dataset_dict['dataset_preview'] = vd._DATASET_PREVIEW_FIRST_RESOURCE
                else:
                    self.dataset_dict['dataset_preview'] = vd._DATASET_PREVIEW_RESOURCE_ID
            else:
                self.dataset_dict['dataset_preview'] = vd._DATASET_PREVIEW_NO_PREVIEW
        else:
            self.dataset_dict['dataset_preview'] = vd._DATASET_PREVIEW_NO_PREVIEW

    def process_resource_grouping_save(self):
        if self.dataset_dict.get('resource_grouping'):
            self.dataset_dict['resource_grouping'] = self.dataset_dict.get('resource_grouping').split(u', ')

    def process_private_and_req_data(self):
        if 'private' not in self.dataset_dict:
            self.dataset_dict['private'] = 'True'
        else:
            if self.dataset_dict.get('private') == 'public':
                self.dataset_dict['private'] = 'False'
            if self.dataset_dict.get('private') == 'private':
                self.dataset_dict['private'] = 'True'
            if self.dataset_dict.get('private') == 'requestdata':
                self.dataset_dict['private'] = 'False'
                self.dataset_dict['is_requestdata_type'] = 'True'
