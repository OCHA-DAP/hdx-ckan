'''
Created on Dec 22, 2014

@author: alexandru-m-g
'''


import ckan.lib.base as base
import ckan.model as model
import ckan.lib.helpers as h

class BrowseController(base.BaseController):
    
    def index(self):
        return base.render('browse/browse.html')