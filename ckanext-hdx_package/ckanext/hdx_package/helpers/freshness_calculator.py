import datetime
import dateutil.parser
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

    @staticmethod
    def dataset_last_change_date(dataset_dict):
        '''
        :param dataset_dict:
        :type dataset_dict: dict
        :return:
        :rtype: datetime.datetime
        '''
        last_change_date = None
        last_modified = dataset_dict.get('last_modified')
        reviewed = dataset_dict.get('review_date')
        if not last_modified or not reviewed:
            last = last_modified or reviewed
            if last:
                last_change_date = dateutil.parser.parse(last)
        else:
            last_modified_date = dateutil.parser.parse(last_modified)
            review_date = dateutil.parser.parse(reviewed)
            last_change_date = last_modified_date if last_modified_date > review_date else review_date

        last_change_date = last_change_date.replace(tzinfo=None) if last_change_date else None
        return last_change_date

    def __init__(self, dataset_dict):
        self.surely_not_fresh = True
        self.dataset_dict = dataset_dict
        update_freq = dataset_dict.get('data_update_frequency')
        # modified = dataset_dict.get('metadata_modified')
        try:
            self.modified = FreshnessCalculator.dataset_last_change_date(dataset_dict)
            if self.modified and update_freq and UPDATE_FREQ_INFO.get(update_freq):
                # if '.' not in modified:
                #     modified += '.000'
                # self.modified = datetime.datetime.strptime(modified, "%Y-%m-%dT%H:%M:%S.%f")
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
