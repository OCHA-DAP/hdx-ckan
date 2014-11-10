'''
Created on Nov 3, 2014

@author: alexandru-m-g
'''

import logging
import ckan.plugins as plugins
import ckan.plugins.toolkit as tk
import ckan.lib.plugins as lib_plugins

class HDXCrisisPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IRoutes, inherit=True)
    
    def before_map(self, map):
        map.connect('show_crisis', '/ebola', controller='ckanext.hdx_crisis.controllers.crisis_controller:CrisisController', action='show')
        return map
     