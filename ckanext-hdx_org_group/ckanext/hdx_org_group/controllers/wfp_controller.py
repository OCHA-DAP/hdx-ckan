'''
Created on Jan 13, 2015

@author: alexandru-m-g
'''


import logging

import ckan.lib.base as base
import ckan.logic as logic
import ckan.model as model
import ckan.common as common

import ckanext.hdx_search.controllers.simple_search_controller as simple_search_controller

render = base.render
abort = base.abort
NotFound = logic.NotFound
NotAuthorized = logic.NotAuthorized
get_action = logic.get_action
c = common.c
request = common.request
_ = common._


log = logging.getLogger(__name__)

class WfpController(simple_search_controller.HDXSimpleSearchController):

    def read(self):

        template_data = {
            'data': {
                'message' : 'Test message'
            },
            'errors': None,
            'error_summary': None,
        }

        result = render('organization/custom/wfp.html', extra_vars=template_data)

        return result