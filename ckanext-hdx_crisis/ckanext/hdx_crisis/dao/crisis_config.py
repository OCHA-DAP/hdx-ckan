'''
Created on Jun 18, 2015

@author: dan
'''
import pylons.config as config

c_ebola = config.get('hdx.crisis.ebola')
c_nepal_earthquake = config.get('hdx.crisis.nepal_earthquake')
CRISES = [c_ebola, c_nepal_earthquake]


class CrisisConfig:
    """
        Used for different customizations required by crises specifics.
        It will be extended by specific classes
    """

    def __init__(self):
        self.is_crisis = True
        self.processed_data = None

    @staticmethod
    def get_crises(label):
        import ckanext.hdx_crisis.dao.nepal_crisis_config as nepal_crisis_config

        if label == c_nepal_earthquake:
            return nepal_crisis_config.NepalCrisisConfig()
        return None

    def process_config(self, template_data=None):
        """
            Used to process, transform and add data for each crisis
        :return:
        """
        pass
