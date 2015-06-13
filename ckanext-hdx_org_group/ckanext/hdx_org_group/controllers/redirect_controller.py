'''
Created on Aug 7, 2014

@author: alexandru-m-g
'''

import ckan.lib.base as base
import ckan.lib.helpers as h


class RedirectController(base.BaseController):
    def redirect_to_org_list(self, id=None):
        h.redirect_to(controller='organization', action='index')
        
        