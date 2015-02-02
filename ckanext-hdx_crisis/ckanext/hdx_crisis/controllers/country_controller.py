'''
Created on Dec 2, 2014

@author: alexandru-m-g
'''

import logging

import ckan.lib.base as base
import ckan.model as model
import ckan.common as common
import ckanext.hdx_crisis.dao.country_data_access as country_data_access
import ckanext.hdx_theme.helpers.top_line_items_formatter as formatters


render = base.render
c = common.c

import ckanext.hdx_crisis.controllers.crisis_controller as controllers

log = logging.getLogger(__name__)


class CountryController(controllers.CrisisController):

    def show(self):

        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'for_view': True,
                   'auth_user_obj': c.userobj}

        crisis_data_access = country_data_access.ColombiaCrisisDataAccess()
        crisis_data_access.fetch_data(context)
        c.top_line_items = crisis_data_access.get_top_line_items()

        formatter = formatters.TopLineItemsFormatter(c.top_line_items)
        formatter.format_results()

        search_params = {u'groups': u'col'}

        self._generate_dataset_results(
            context, search_params, action_alias='show_country')

        self._generate_other_links(search_params)

        return render('country/colombia.html')
