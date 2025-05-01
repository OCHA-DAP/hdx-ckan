import datetime
import logging
from collections import OrderedDict

import dateutil.parser
from six import text_type
import ckan.plugins.toolkit as tk
from ckanext.hdx_package.helpers.extras import get_extra_from_dataset

log = logging.getLogger(__name__)
h=tk.h
UPDATE_FREQ_LIVE = '0'
UPDATE_FREQ_AS_NEEDED = '-2'
UPDATE_FREQ_NEVER = '-1'

UPDATE_FREQ_INFO = OrderedDict(
    (
        ('1', {'title': 'Every day', 'special': False}),
        ('2', {'title': 'Every two days', 'special': False}),
        ('7', {'title': 'Every week', 'special': False}),
        ('14', {'title': 'Every two weeks', 'special': False}),
        ('30', {'title': 'Every month', 'special': False}),
        ('60', {'title': 'Every two months', 'special': False}),
        ('90', {'title': 'Every three months', 'special': False}),
        ('120', {'title': 'Every fourth months', 'special': False}),
        ('180', {'title': 'Every six months', 'special': False}),
        ('300', {'title': 'Every ten months', 'special': False}),
        ('365', {'title': 'Every year', 'special': False}),
        ('730', {'title': 'Every two years', 'special': False}),
        (UPDATE_FREQ_LIVE, {'title': 'Live', 'special': True}),
        (UPDATE_FREQ_AS_NEEDED, {'title': 'As needed', 'special': True}),
        (UPDATE_FREQ_NEVER, {'title': 'Never', 'special': True}),
    )
)

FRESHNESS_PROPERTY = 'is_fresh'

UPDATE_STATUS_PROPERTY = 'update_status'
UPDATE_STATUS_URL_FILTER = 'ext_' + UPDATE_STATUS_PROPERTY

UPDATE_STATUS_FRESH = 'fresh'
UPDATE_STATUS_UNKNOWN = 'unknown'
UPDATE_STATUS_NEEDS_UPDATE = 'needs_update'

DELTA_END_DATASET_DATE_INFINITE_DAYS = 365*100

def get_calculator_instance(dataset_dict, type='for-data-completeness'):
    # if type == 'for-data-completeness':
    #     return DataCompletenessFreshnessCalculator(dataset_dict)
    # else:
    return FreshnessCalculator(dataset_dict)


class FreshnessCalculator(object):

    def __init__(self, dataset_dict):

        self.surely_not_fresh = True
        self.dataset_dict = dataset_dict
        update_freq = get_extra_from_dataset('data_update_frequency', dataset_dict)
        try:
            dataset_date = get_extra_from_dataset('dataset_date', dataset_dict)
            self.end_dataset_date, self.is_end_dataset_date_star = h.hdx_end_of_dataset_date(dataset_date)
            if not self.end_dataset_date:
                due_date = dataset_dict.get('due_date')
                if due_date and 'Z' in due_date:
                    self.end_dataset_date = self._compute_due_date(due_date, update_freq)
                    # due_date = due_date.replace('Z', '')
                    # due_date = dateutil.parser.parse(due_date)
                    # _update_freq = int(update_freq)
                    # if self.is_end_dataset_date_star or not _update_freq or _update_freq == -1:
                    #     due_date = (
                    #         self.end_dataset_date - datetime.timedelta(days=DELTA_END_DATASET_DATE_INFINITE_DAYS)
                    #     ).replace(microsecond=0)
                    # else:
                    #     due_date = (
                    #         self.end_dataset_date - datetime.timedelta(days=_update_freq)
                    #     ).replace(microsecond=0)
                    # self.end_dataset_date = due_date

            if self.end_dataset_date and update_freq:
                self.update_freq_in_days = int(update_freq)
                self.surely_not_fresh = False
        except Exception as e:
            log.error(text_type(e))

    def _compute_due_date(self, due_date, update_freq):
        if due_date and 'Z' in due_date:
            due_date = due_date.replace('Z', '')
            due_date = dateutil.parser.parse(due_date)
            _update_freq = int(update_freq)
            if self.is_end_dataset_date_star or not _update_freq or _update_freq == -1:
                due_date = (
                    due_date - datetime.timedelta(days=DELTA_END_DATASET_DATE_INFINITE_DAYS)
                ).replace(microsecond=0)
            else:
                due_date = (due_date - datetime.timedelta(days=_update_freq)).replace(microsecond=0)
            return due_date

    def is_fresh(self, now=datetime.datetime.utcnow()):
        """
        Using utcnow because this is used by core ckan, see ckan.model.package
        :return: True if fresh, otherwise False
        :rtype: bool
        """
        update_freq = get_extra_from_dataset('data_update_frequency', self.dataset_dict)
        if update_freq == UPDATE_FREQ_LIVE:
            return True
        if update_freq == UPDATE_FREQ_NEVER or update_freq == UPDATE_FREQ_AS_NEEDED:
            return False

        start_of_expiration = self.compute_range_beginnings()
        if start_of_expiration:
            now = datetime.datetime.utcnow() # using utcnow bc this is used by core ckan, see ckan.model.package
            fresh = now < start_of_expiration
            return fresh
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
        update_freq = get_extra_from_dataset('data_update_frequency', self.dataset_dict)
        if update_freq == UPDATE_FREQ_LIVE or update_freq == UPDATE_FREQ_NEVER or update_freq == UPDATE_FREQ_AS_NEEDED:
            self.dataset_dict['due_date'] = None
        else:
            start_of_due_range= self.compute_range_beginnings()
            if start_of_due_range:
                self.dataset_dict['due_date'] = start_of_due_range.isoformat()

    def compute_range_beginnings(self):
        if not self.surely_not_fresh:
            if self.is_end_dataset_date_star or not self.update_freq_in_days or self.update_freq_in_days == -1:
                start_of_due_range = (
                    self.end_dataset_date + datetime.timedelta(days=DELTA_END_DATASET_DATE_INFINITE_DAYS)
                ).replace(microsecond=0)
            else:
                start_of_due_range = (self.end_dataset_date + datetime.timedelta(days=self.update_freq_in_days))\
                .replace(microsecond=0)
            return start_of_due_range #, start_of_overdue_range #, start_of_delinquent_range
        else:
            return None

    def read_due_overdue_dates(self):
        try:
            if 'due_date' in self.dataset_dict:
                update_freq = get_extra_from_dataset('data_update_frequency', self.dataset_dict)
                if update_freq == UPDATE_FREQ_LIVE or update_freq == UPDATE_FREQ_NEVER or update_freq == UPDATE_FREQ_AS_NEEDED:
                    return None
                due_date_str = self.dataset_dict.get('due_date')
                due_date = dateutil.parser.parse(due_date_str[0:-1])
                # overdue_date_str = self.dataset_dict.get('overdue_date')
                # overdue_date = dateutil.parser.parse(overdue_date_str[0:-1])
                return due_date #, overdue_date
        except Exception as e:
            log.warn(str(e))
        return None
