'''
Created on Jun 20, 2014

@author: alexandru-m-g
'''

import ckan.lib.base as base

class HDXPreselectOrgController(base.BaseController):
    def preselect(self):
        return base.render('organization/request_mem_or_org.html')
