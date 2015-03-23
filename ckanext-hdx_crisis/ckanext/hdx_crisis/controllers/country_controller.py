'''
Created on Dec 2, 2014

@author: alexandru-m-g
'''

import logging
import pylons.config as config

import ckan.lib.base as base
import ckan.model as model
import ckan.common as common
import ckan.logic as logic

import ckanext.hdx_crisis.dao.country_data_access as country_data_access
import ckanext.hdx_theme.helpers.top_line_items_formatter as formatters
import ckanext.hdx_crisis.controllers.crisis_controller as controllers
import ckan.controllers.group as group

render = base.render
c = common.c
get_action = logic.get_action


log = logging.getLogger(__name__)


class CountryController(group.GroupController, controllers.CrisisController):

    def read(self, id):

        group_info = self.get_group(id)

        custom_options = {
            'top_line_resource_id': config.get('hdx.colombia.datastore.top_line_num'),
            'chart1_datastore_id': config.get('hdx.colombia.datastore.displaced'),
            'chart2_datastore_id': config.get('hdx.colombia.datastore.access_constraints')
        }

        template_data = self.generate_template_data(group_info.get('name', id), custom_options)

        return render('country/custom_country.html', extra_vars=template_data)

    def get_group(self, id):
        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author,
                   'schema': self._db_to_form_schema(group_type='group'),
                   'include_datasets': False,
                   'for_view': True}
        data_dict = {'id': id}

        group_info = get_action('hdx_light_group_show')(context, data_dict)

        return group_info

    def generate_template_data(self, org_name, custom_options):

        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'for_view': True,
                   'auth_user_obj': c.userobj}

        top_line_resource_id = custom_options.get('top_line_resource_id', None)
        top_line_items = self.get_top_line_numbers(top_line_resource_id)

        search_params = {u'groups': org_name}

        self._generate_dataset_results(
            context, search_params, action_alias='show_custom_country', other_params_dict={'id': org_name} )

        self._generate_other_links(search_params)

        template_data = {
            'data': {
                'top_line_items': top_line_items,
                'chart1_datastore_id': custom_options.get('chart1_datastore_id', None),
                'chart2_datastore_id': custom_options.get('chart2_datastore_id', None)
            },
            'errors': None,
            'error_summary': None,
        }

        return template_data

    def get_top_line_numbers(self, top_line_resource_id):
        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'for_view': True,
                   'auth_user_obj': c.userobj}

        crisis_data_access = country_data_access.ColombiaCrisisDataAccess(top_line_resource_id)
        crisis_data_access.fetch_data(context)
        top_line_items = crisis_data_access.get_top_line_items()

        formatter = formatters.TopLineItemsFormatter(top_line_items)
        formatter.format_results()

        return top_line_items
