'''
Created on Dec 2, 2014

@author: alexandru-m-g
updated by dan on Jun 22, 2015
'''

import logging
import math
import pylons.config as config

import ckan.lib.base as base
import ckan.model as model
import ckan.common as common
import ckan.logic as logic
import ckanext.hdx_crisis.controllers.custom_location_controller as custom_location_controller
#import ckanext.hdx_crisis.dao.country_data_access as country_data_access
import ckanext.hdx_org_group.dao.indicator_access as indicator_access
import ckanext.hdx_theme.helpers.top_line_items_formatter as formatters
#import ckanext.hdx_theme.helpers.helpers as helpers
#import ckanext.hdx_crisis.dao.crisis_config as crisis_config
import ckanext.hdx_crisis.dao.ebola_crisis_data_access as ebola_crisis_data_access

EbolaCrisisDataAccess = ebola_crisis_data_access.EbolaCrisisDataAccess
CustomLocationController = custom_location_controller.CustomLocationController

render = base.render
c = common.c
get_action = logic.get_action
json = common.json
_ = common._

log = logging.getLogger(__name__)

IndicatorAccess = indicator_access.IndicatorAccess


class EbolaCustomLocationController(CustomLocationController):
    '''
    Extends Group and Crisis Controller and is used by custom locations to populate
    and compute the data to be displayed
    '''

    def read(self):
        template_data = self._generate_ebola_template_data()
        return render('crisis/crisis-ebola.html', extra_vars=template_data)

    def _generate_ebola_template_data(self):
        '''
        Compute all the data related to Ebola crisis.
        :return: renders the crisis-ebola.html template with data computed about Ebola
        '''

        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'for_view': True,
                   'auth_user_obj': c.userobj}

        top_line_res_id = config.get('hdx.ebola.datastore.top_line_num')
        cases_res_id = config.get('hdx.ebola.datastore.cases')
        appeal_res_id = config.get('hdx.ebola.datastore.appeal')

        crisis_data_access = EbolaCrisisDataAccess(top_line_res_id, cases_res_id, appeal_res_id)
        crisis_data_access.fetch_data(context)
        top_line_items = crisis_data_access.get_top_line_items()

        formatter = formatters.TopLineItemsWithDateFormatter(top_line_items)
        formatter.format_results()

        search_params = {'q': u'ebola'}

        self._generate_dataset_results(context, search_params)

        self._generate_other_links(search_params)

        template_data = {
            'data': {
                'top_line_items': top_line_items,
                'cases_datastore_id': cases_res_id
            },
            'errors': None,
            'error_summary': None,
        }

        return template_data
