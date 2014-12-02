'''
Created on Dec 2, 2014

@author: alexandru-m-g
'''

import logging

import ckan.lib.base as base
import ckan.model as model
import ckan.common as common

import ckanext.hdx_crisis.dao.data_access as data_access
import ckanext.hdx_crisis.formatters.top_line_items_formatter as formatters


render = base.render
c = common.c

import ckanext.hdx_crisis.controllers.crisis_controller as controllers

log = logging.getLogger(__name__)


class CountryController(controllers.CrisisController):

    def show(self):

        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'for_view': True,
                   'auth_user_obj': c.userobj}

        crisis_data_access = data_access.EbolaCrisisDataAccess()
        crisis_data_access.fetch_data(context)
        c.top_line_items = crisis_data_access.get_top_line_items()

        formatter = formatters.TopLineItemsFormatter(c.top_line_items)
        formatter.format_results()

        search_term = u'colombia'

        self._generate_dataset_results(context, search_term)

        self._generate_other_links(search_term)

        return render('country/country.html')
