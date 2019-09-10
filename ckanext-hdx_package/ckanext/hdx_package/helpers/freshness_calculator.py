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


def get_extra_from_dataset(field_name, dataset_dict):
    ALLOWED_EXTRAS = {'review_date', 'data_update_frequency'}
    result = None
    if field_name in dataset_dict:
        result = dataset_dict[field_name]

    # When a dataset is indexed in solr the package dict returned by package_show
    # leaves the extras fields unprocessed in an extras list so that they get indexed as extras_* fields in solr
    elif 'extras' in dataset_dict and field_name in ALLOWED_EXTRAS:
        result = next(
            (extra.get('value') for extra in dataset_dict.get('extras')
             if extra.get('state') == 'active' and extra.get('key') == field_name),
            {})

    return result


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
        last_modified = dataset_dict.get('last_modified') # last_modified is not an extra; only stored in solr
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
            if self.modified and update_freq and UPDATE_FREQ_INFO.get(update_freq):
                # if '.' not in modified:
                #     modified += '.000'
                # self.modified = datetime.datetime.strptime(modified, "%Y-%m-%dT%H:%M:%S.%f")
                self.extra_days = UPDATE_FREQ_INFO.get(update_freq)
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
        start_of_overdue_range = self.compute_range_beginnings()[1]
        if start_of_overdue_range:
            now = datetime.datetime.utcnow() # using utcnow bc this is used by core ckan, see ckan.model.package
            fresh = now < start_of_overdue_range
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
        self.dataset_dict[FRESHNESS_PROPERTY] = self.is_fresh()

    def populate_with_date_ranges(self):
        start_of_due_range, start_of_overdue_range = self.compute_range_beginnings()
        if start_of_due_range and start_of_overdue_range:
            self.dataset_dict['due_daterange'] = \
                '[{}Z TO {}Z]'.format(start_of_due_range.isoformat(), start_of_overdue_range.isoformat())

            self.dataset_dict['overdue_daterange'] = '[{}Z TO *]'.format(start_of_overdue_range.isoformat())

    def compute_range_beginnings(self):
        if not self.surely_not_fresh:
            start_of_due_range = (self.modified + datetime.timedelta(days=self.update_freq_in_days)).replace(
                microsecond=0)
            start_of_overdue_range = (start_of_due_range + datetime.timedelta(days=self.extra_days)).replace(microsecond=0)
            return start_of_due_range, start_of_overdue_range
        else:
            return None, None
