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


class CustomCountryController(group.GroupController, controllers.CrisisController):

    def read(self, id):

        group_info = self.get_group(id)

        template_data = self.generate_template_data(group_info)

        return render('country/custom_country.html', extra_vars=template_data)

    # Will soon be removed
    def show(self):
        return self.read(u'col')

    def get_group(self, id):
        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author,
                   'schema': self._db_to_form_schema(group_type='group'),
                   'include_datasets': False,
                   'for_view': True}
        data_dict = {'id': id}

        group_info = get_action('hdx_light_group_show')(context, data_dict)

        return group_info

    def _get_top_line_datastore_id(self, group_info):
        return config.get('hdx.colombia.datastore.top_line_num')

    def _get_charts_config(self, group_info):
        return [
            {
                'title': 'Number of Internally Displaced People',
                'type': 'bar',
                'title_x': 'Test x title',
                'title_y': 'Persons',
                'sources': [
                    {
                        'datastore_id': config.get('hdx.colombia.datastore.displaced'),
                        'title': 'Number of displaced ...',
                        'orgName': 'OCHA',
                        'url':'',
                        'column_x': 'Year',
                        'column_y': 'Persons'
                    },
                    {
                        'datastore_id': config.get('hdx.colombia.datastore.displaced'),
                        'title': 'Number of malaria ...',
                        'orgName': 'OCHA',
                        'url':'',
                        'column_x': 'Year',
                        'column_y': 'Persons'
                    }
                ]
            },
            {
                'title': 'Number of People with Access Constraints',
                'type': 'bar',
                'title_x': 'Sample title x-axis',
                'title_y': 'Persons',
                'sources': [
                    {
                        'datastore_id': config.get('hdx.colombia.datastore.access_constraints'),
                        'Title': 'Title',
                        'orgName': 'OCHA',
                        'url': '',
                        'column_x': 'Date',
                        'column_y': 'Persons'
                    }
                ]
            }
        ]

    def _get_maps_config(self, group_info):
        return {
            'boundries_datastore_id': 'boundries_datastore_id',
            'boundries_join_column': 'boundries_join_column',
            'facts_datastore_id': 'facts_datastore_id',
            'facts_join_column': 'facts_join_column'
        }

    def generate_template_data(self, group_info):

        country_name = group_info['name']

        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'for_view': True,
                   'auth_user_obj': c.userobj}

        top_line_resource_id = self._get_top_line_datastore_id(group_info)
        top_line_items = self.get_top_line_numbers(top_line_resource_id)

        search_params = {u'groups': country_name}

        self._generate_dataset_results(
            context, search_params, action_alias='show_custom_country', other_params_dict={'id': country_name} )

        self._generate_other_links(search_params)

        template_data = {
            'data': {
                'country_title': group_info.get('title', group_info['name']),
                'top_line_items': top_line_items,
                'charts': self._get_charts_config(group_info),
                'map': self._get_maps_config(group_info)
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
