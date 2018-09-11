import datetime
import logging

log = logging.getLogger(__name__)

UPDATE_FREQ_INFO = {
    '1': 1,
    '7': 7,
    '14': 7,
    '30': 14,
    '90': 30,
    '180': 30,
    '365': 60,
}

FRESHNESS_PROPERTY = 'is_fresh'


class FreshnessCalculator(object):

    def __init__(self, dataset_dict):
        self.surely_not_fresh = True
        self.dataset_dict = dataset_dict
        update_freq = dataset_dict.get('data_update_frequency')
        modified = dataset_dict.get('metadata_modified')
        try:
            if update_freq and UPDATE_FREQ_INFO.get(update_freq):
                if modified.endswith('Z'):
                    modified = modified.replace('Z', '')
                self.modified = datetime.datetime.strptime(modified, "%Y-%m-%dT%H:%M:%S.%f")
                self.extra_days = UPDATE_FREQ_INFO.get(update_freq)
                self.update_freq_in_days = int(update_freq)
                self.surely_not_fresh = False
        except Exception, e:
            log.error(unicode(e))

    def is_fresh(self):
        '''
        :return: True if fresh, otherwise False
        :rtype: bool
        '''
        if not self.surely_not_fresh:
            now = datetime.datetime.utcnow()
            difference = now - self.modified
            fresh = difference.days < self.update_freq_in_days + self.extra_days
            return fresh
        else:
            return False

    def populate_with_freshness(self):
        self.dataset_dict[FRESHNESS_PROPERTY] = self.is_fresh()
