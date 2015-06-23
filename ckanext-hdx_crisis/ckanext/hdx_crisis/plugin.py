'''
Created on Nov 3, 2014

@author: alexandru-m-g
'''

import logging
import ckan.plugins as plugins

import ckanext.hdx_crisis.controllers.custom_location_controller as custom_location_controller


class HDXCrisisPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IRoutes, inherit=True)

    def before_map(self, map):
        # map.connect('show_crisis', '/ebola',
        #             controller='ckanext.hdx_crisis.controllers.crisis_controller:CrisisController', action='show')
        map.connect('show_crisis', '/ebola',
                    controller='ckanext.hdx_crisis.controllers.ebola_custom_location_controller:EbolaCustomLocationController', action='read',
                    )

        map.connect('show_crisis', '/group/ebola',
                    controller='ckanext.hdx_crisis.controllers.ebola_custom_location_controller:EbolaCustomLocationController', action='read',
                    )

        # map.connect('show_country', '/group/col',
        #             controller='ckanext.hdx_crisis.controllers.custom_location_controller:CustomLocationController', action='show')
        map.connect('show_custom_country', '/group/{id}',
                    controller='ckanext.hdx_crisis.controllers.custom_location_controller:CustomLocationController', action='read',
                    conditions={'function': custom_location_controller.is_custom})
        return map
