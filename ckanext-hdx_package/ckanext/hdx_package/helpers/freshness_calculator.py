import datetime
import logging

import dateutil.parser
from ckanext.hdx_package.helpers.extras import get_extra_from_dataset

log = logging.getLogger(__name__)

UPDATE_FREQ_OVERDUE_INFO = {
    '1': 1,
    '7': 7,
    '14': 7,
    '30': 14,
    '90': 30,
    '180': 30,
    '365': 60,
}

UPDATE_FREQ_DELINQUENT_INFO = {
    '1': 2,
    '7': 14,
    '14': 14,
    '30': 30,
    '90': 60,
    '180': 60,
    '365': 90,
}

FRESHNESS_PROPERTY = 'is_fresh'

UPDATE_STATUS_PROPERTY = 'update_status'
UPDATE_STATUS_URL_FILTER = 'ext_' + UPDATE_STATUS_PROPERTY

UPDATE_STATUS_FRESH = 'fresh'
UPDATE_STATUS_UNKNOWN = 'unknown'
UPDATE_STATUS_NEEDS_UPDATE = 'needs_update'


def get_calculator_instance(dataset_dict, type=None):
    if type == 'for-data-completeness':
        return DataCompletenessFreshnessCalculator(dataset_dict)
    else:
        return FreshnessCalculator(dataset_dict)


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
        last_modified = dataset_dict.get('last_modified')  # last_modified is not an extra; only stored in solr
        reviewed = get_extra_from_dataset('review_date', dataset_dict) # dataset_dict.get('review_date')
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
        update_freq = get_extra_from_dataset('data_update_frequency', dataset_dict)
        # modified = dataset_dict.get('metadata_modified')
        try:
            self.modified = FreshnessCalculator.dataset_last_change_date(dataset_dict)
            if self.modified and update_freq and UPDATE_FREQ_OVERDUE_INFO.get(update_freq):
                # if '.' not in modified:
                #     modified += '.000'
                # self.modified = datetime.datetime.strptime(modified, "%Y-%m-%dT%H:%M:%S.%f")
                self.extra_overdue_days = UPDATE_FREQ_OVERDUE_INFO.get(update_freq)
                self.extra_delinquent_days = UPDATE_FREQ_DELINQUENT_INFO[update_freq]
                self.update_freq_in_days = int(update_freq)
                self.surely_not_fresh = False
        except Exception, e:
            log.error(unicode(e))

    def is_fresh(self, now=datetime.datetime.utcnow()):
        '''
        Using utcnow because this is used by core ckan, see ckan.model.package
        :return: True if fresh, otherwise False
        :rtype: bool
        '''
        start_of_expiration = self.compute_range_beginnings()[0]
        if start_of_expiration:
            now = datetime.datetime.utcnow() # using utcnow bc this is used by core ckan, see ckan.model.package
            fresh = now < start_of_expiration
            return fresh
        else:
            return False

    def is_overdue(self, now=datetime.datetime.utcnow()):
        '''
        This might seem like (not is_fresh()) but the definition of fresh in CKAN might change
        so implementing this separately
        Using utcnow because this is used by core ckan, see ckan.model.package
        :return: True if overdue, otherwise False
        :rtype: bool
        '''
        start_of_overdue_range = self.compute_range_beginnings()[1]
        if start_of_overdue_range:
            overdue = now > start_of_overdue_range
            return overdue
        else:
            return False

    def populate_with_freshness(self):
        is_fresh = self.is_fresh()
        self.dataset_dict[FRESHNESS_PROPERTY] = is_fresh

        if is_fresh:
            self.dataset_dict[UPDATE_STATUS_PROPERTY] = UPDATE_STATUS_FRESH
        elif self.dataset_dict.get('due_date'):
            self.dataset_dict[UPDATE_STATUS_PROPERTY] = UPDATE_STATUS_NEEDS_UPDATE
        else:
            self.dataset_dict[UPDATE_STATUS_PROPERTY] = UPDATE_STATUS_UNKNOWN

    def populate_with_date_ranges(self):
        start_of_due_range, start_of_overdue_range, start_of_delinquent_range = self.compute_range_beginnings()
        if start_of_due_range and start_of_overdue_range:
            self.dataset_dict['due_date'] = start_of_due_range.isoformat()
            self.dataset_dict['overdue_date'] = start_of_overdue_range.isoformat()
            self.dataset_dict['delinquent_date'] = start_of_delinquent_range.isoformat()
            # self.dataset_dict['due_daterange'] = \
            #     '[{}Z TO {}Z]'.format(start_of_due_range.isoformat(), start_of_overdue_range.isoformat())
            #
            # self.dataset_dict['overdue_daterange'] = '[{}Z TO *]'.format(start_of_overdue_range.isoformat())

    def compute_range_beginnings(self):
        if not self.surely_not_fresh:
            start_of_due_range = (self.modified + datetime.timedelta(days=self.update_freq_in_days))\
                .replace(microsecond=0)
            start_of_overdue_range = (start_of_due_range + datetime.timedelta(days=self.extra_overdue_days))\
                .replace(microsecond=0)
            start_of_delinquent_range = (start_of_due_range + datetime.timedelta(days=self.extra_delinquent_days))\
                .replace(microsecond=0)
            return start_of_due_range, start_of_overdue_range, start_of_delinquent_range
        else:
            return None, None, None

    def read_due_overdue_dates(self):
        try:
            # if 'due_daterange' in self.dataset_dict:
            #     range_str = self.dataset_dict.get('due_daterange')
            #     range = range_str[1:-1].split(' TO ')
            #     if len(range) == 2:
            #         due_date = dateparser.parse(range[0][0:-1])
            #         overdue_date = dateparser.parse(range[1][0:-1])
            #         return due_date, overdue_date
            if 'due_date' in self.dataset_dict:
                due_date_str = self.dataset_dict.get('due_date')
                due_date = dateutil.parser.parse(due_date_str[0:-1])
                overdue_date_str = self.dataset_dict.get('overdue_date')
                overdue_date = dateutil.parser.parse(overdue_date_str[0:-1])
                return due_date, overdue_date
        except Exception as e:
            log.warn(str(e))
        return None, None


class DataCompletenessFreshnessCalculator(FreshnessCalculator):

    def is_fresh(self, now=datetime.datetime.utcnow()):
        update_freq = get_extra_from_dataset('data_update_frequency', self.dataset_dict)
        try:
            if update_freq is not None and int(update_freq) <= 0:
                return True
        except ValueError as e:
            log.info('Update frequency for dataset "{}" is not a number'.format(self.dataset_dict.get('name')))

        return super(DataCompletenessFreshnessCalculator, self).is_fresh(now)

