'''
Created on Nov 3, 2014

@author: alexandru-m-g
'''

import logging
import ckan.plugins as plugins

import ckanext.hdx_crisis.controllers.custom_country_controller as custom_country_controller


class HDXCrisisPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IRoutes, inherit=True)

    def before_map(self, map):
        map.connect('show_crisis', '/ebola',
                    controller='ckanext.hdx_crisis.controllers.crisis_controller:CrisisController', action='show')
        map.connect('show_crisis', '/nepal-earthquake',
                    controller='ckanext.hdx_crisis.controllers.crisis_controller:CrisisController', action='show')
        # map.connect('show_country', '/group/col',
        #             controller='ckanext.hdx_crisis.controllers.custom_country_controller:CustomCountryController', action='show')
        map.connect('show_custom_country', '/group/{id}',
                    controller='ckanext.hdx_crisis.controllers.custom_country_controller:CustomCountryController', action='read',
                    conditions={'function': custom_country_controller.is_custom})
        return map
