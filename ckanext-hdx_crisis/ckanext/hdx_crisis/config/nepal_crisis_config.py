'''
Created on Jun 18, 2015

@author: dan
'''

import ckanext.hdx_crisis.config.crisis_config as crisis_config
import pylons.config as config


class NepalCrisisConfig(crisis_config.CrisisConfig):
    """
        Used for Nepal Crisis
    """

    def process_config(self, template_data):
        """
            Used to process, transform and add data for each crisis

        """
        template_data['is_crisis'] = True
        template_data['map']['is_crisis'] = 'true'
        template_data['map']['basemap_url'] = config.get('hdx.crisismap.url')
        template_data['map']['circle_markers'] = config.get('hdx.nepal_earthquake.filestore.circle_markers')
        template_data['map']['shakemap'] = config.get('hdx.nepal_earthquake.filestore.shakemap')
