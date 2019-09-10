import logging
import json
import datetime
import dateutil.parser

import ckan.plugins.toolkit as tk

import ckanext.hdx_user_extra.model as ue_model
from ckanext.hdx_theme.helpers.exception import BaseHdxException
from ckanext.hdx_users.helpers.helpers import find_user_id
from ckanext.hdx_package.helpers.freshness_calculator import FreshnessCalculator

log = logging.getLogger(__name__)
get_action = tk.get_action

DOMAIN_FRESHNESS = 'freshness'
DOMAINS = {DOMAIN_FRESHNESS}


class FreshnessNotificationsChecker(object):

    DASHBOARD_VIEWED = 'dashboard_viewed'

    def __init__(self, username_or_id):
        super(FreshnessNotificationsChecker, self).__init__()
        self.notification_info = NotificationsInfo(username_or_id)

    @property
    def user_id(self):
        return self.notification_info.user_id

    def get_freshness_data(self):
        return self.notification_info.get_domain_data(DOMAIN_FRESHNESS, {})

    def get_dashboard_viewed(self):
        viewed_str = self.get_freshness_data().get(FreshnessNotificationsChecker.DASHBOARD_VIEWED)
        if viewed_str:
            return dateutil.parser.parse(viewed_str)
        return None

    def set_freshness_data(self, data):
        return self.notification_info.set_domain_data(DOMAIN_FRESHNESS, data)

    def set_dashboard_viewed(self, viewed_date):
        '''
        :param viewed_date:
        :type viewed_date: datetime.datetime
        '''
        self.set_freshness_data({FreshnessNotificationsChecker.DASHBOARD_VIEWED: viewed_date.isoformat()})

    def has_unseen_overdue_datasets(self):

        now = datetime.datetime.now().replace(minute=0, second=0, microsecond=0)
        second_from_now = now + datetime.timedelta(seconds=1)
        query_string = 'maintainer:{} AND overdue_daterange:[{}Z TO {}Z]'.format(self.user_id, now.isoformat(),
                                                                                 second_from_now.isoformat())
        viewed_date = self.get_dashboard_viewed()
        if viewed_date:
            # eliminate the datasets that were already overdue last time the user looked
            second_from_viewed_date = viewed_date + datetime.timedelta(seconds=1)
            query_string += ' AND -overdue_daterange:[{}Z TO {}Z]'.format(viewed_date.isoformat(),
                                                                          second_from_viewed_date.isoformat())
        query_string = '(' + query_string + ')'
        query_params = {
            'start': 0,
            'rows': 1,
            'fq': query_string
        }
        search_result = get_action('package_search')({}, query_params)
        num_of_datasets = search_result.get('count', 0)

        if num_of_datasets > 0:
            return True

        return False


class NotificationsInfo(object):

    USER_EXTRA_FIELD = 'hdx_notifications'

    def __init__(self, username_or_id):
        super(NotificationsInfo, self).__init__()
        self.user_id = find_user_id(username_or_id)

    def has_notification_property(self):
        if self.user_id:
            user_extra = ue_model.UserExtra.get(self.user_id, NotificationsInfo.USER_EXTRA_FIELD)
            if user_extra:
                return True
        return False

    def set_domain_data(self, domain, data):

        if domain not in DOMAINS:
            raise WrongDomainNameException('Wrong domain name specified. "{}" is not a valid value'.format(domain))

        try:
            new_user_extra = False
            all_notification_data = self.get_all_data().get(domain, {})
        except NotificationUserExtraNotFound:
            new_user_extra = True
            all_notification_data = {}

        all_notification_data[domain] = data
        all_notification_data_json = json.dumps(all_notification_data)

        data_dict = {
            'user_id': self.user_id,
            'extras': [
                {
                    'key': NotificationsInfo.USER_EXTRA_FIELD,
                    'value': all_notification_data_json,
                    'new_value': all_notification_data_json
                }
            ]
        }
        action = 'user_extra_create' if new_user_extra else 'user_extra_update'
        get_action(action)({'ignore_auth': True}, data_dict)

    def get_all_data(self):
        '''
        :return:
        :rtype: dict
        :raises: NotificationUserExtraNotFound
        '''
        all_notification_data = {}

        user_extra = ue_model.UserExtra.get(self.user_id, NotificationsInfo.USER_EXTRA_FIELD)

        if not user_extra:
            log.info('No notification data found for user {}'.format(self.user_id))
            raise NotificationUserExtraNotFound('Notification user_extra not found for user {}'.format(self.user_id))
        elif user_extra.value:
            try:
                all_notification_data = json.loads(user_extra.value)
            except ValueError as e:
                log.info('No parsable data found in notification user_extra for user {} '
                         'although the user extra entry exists'.format(self.user_id))

        return all_notification_data

    def get_domain_data(self, domain, default_data=None):
        '''
        :param domain:
        :type domain: str
        :param default_data: optional
        :type default_data: dict
        :return:
        :rtype: dict
        '''
        if domain not in DOMAINS:
            raise WrongDomainNameException('Wrong domain name specified. "{}" is not a valid value'.format(domain))

        try:
            all_data = self.get_all_data()
        except NotificationUserExtraNotFound:
            all_data = {}

        return all_data.get(domain, default_data)


class WrongDomainNameException(BaseHdxException):
    pass


class NotificationUserExtraNotFound(BaseHdxException):
    pass
